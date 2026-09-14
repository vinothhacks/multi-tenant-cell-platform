from __future__ import annotations

from .dataplane import copy_tenant_db, secret_path, validate_copy
from .models import MOVE_GATES, Health, LifecycleStatus, Tenant
from .store import Store


class MoveAborted(Exception):
    pass


class MoveCrashed(Exception):
    pass


def start_move(store: Store, tenant: Tenant, target_cell_id: str, reason: str) -> Tenant:
    if tenant.status not in {LifecycleStatus.ACTIVE, LifecycleStatus.MIGRATING, LifecycleStatus.DEGRADED}:
        raise ValueError(f"cannot move from {tenant.status}")
    if target_cell_id not in store.cells:
        raise ValueError("unknown target cell")
    if target_cell_id == tenant.cell_id:
        raise ValueError("already on target cell")

    tenant.source_cell_id = tenant.cell_id
    tenant.move_target_cell_id = target_cell_id
    tenant.move_reason = reason
    tenant.move_committed = False
    tenant.move_gates = {g: False for g in MOVE_GATES}
    tenant.status = LifecycleStatus.MIGRATING_SETUP
    store.audit_event("move_started", tenant_id=tenant.tenant_id, cell_id=target_cell_id, detail={"reason": reason})
    return store.touch(tenant)


def advance_move(
    store: Store,
    tenant: Tenant,
    *,
    abort_before_commit: bool = False,
    crash_before_commit: bool = False,
) -> Tenant:
    src = tenant.source_cell_id or tenant.cell_id
    dest = tenant.move_target_cell_id
    if not dest:
        raise ValueError("no move in progress")

    tenant.status = LifecycleStatus.MIGRATING_SETUP
    copied = copy_tenant_db(store, tenant, dest)
    tenant.move_gates["initial_copy"] = True
    tenant.move_gates["replication"] = True
    store.touch(tenant)

    tenant.status = LifecycleStatus.MIGRATING_CATCHUP
    tenant.move_gates["catch_up"] = True
    tenant.move_gates["lag_zero"] = True
    store.touch(tenant)

    tenant.status = LifecycleStatus.MIGRATING_QUIESCE
    tenant.move_gates["transactions_zero"] = True
    tenant.move_gates["sequences_synced"] = True
    store.touch(tenant)

    tenant.status = LifecycleStatus.MIGRATING_VALIDATE
    src_db = store.tenant_dbs[tenant.tenant_id]
    if not validate_copy(src_db, copied):
        raise ValueError("validation failed")
    tenant.move_gates["validation"] = True
    tenant.move_gates["health_check"] = True
    store.touch(tenant)

    if abort_before_commit:
        tenant.status = LifecycleStatus.ACTIVE
        tenant.move_target_cell_id = None
        store.audit_event("move_aborted_source_authoritative", tenant_id=tenant.tenant_id, cell_id=src)
        return store.touch(tenant)

    if crash_before_commit:
        raise MoveCrashed("before registry commit")

    # Commit point: registry write of cell_id + tenant_version
    tenant.status = LifecycleStatus.CUTOVER
    old_secret = secret_path(src, tenant.tenant_id)
    store.secrets.pop(old_secret, None)
    tenant.cell_id = dest
    tenant.tenant_version += 1
    tenant.secret_version += 1
    copied["cell_id"] = dest
    store.tenant_dbs[tenant.tenant_id] = copied

    store.secrets[secret_path(dest, tenant.tenant_id)] = {
        "role": f"role_{tenant.slug}",
        "database": tenant.database_name,
        "cell_id": dest,
        "secret_version": str(tenant.secret_version),
    }
    store.cache[f"route:{tenant.slug}"] = {
        "tenant_id": tenant.tenant_id,
        "cell_id": dest,
        "tenant_version": tenant.tenant_version,
    }
    tenant.move_gates["epoch_increment"] = True
    tenant.move_gates["routing_switched"] = True
    tenant.move_committed = True
    tenant.status = LifecycleStatus.ACTIVE
    tenant.health = Health.HEALTHY
    store.audit_event(
        "move_committed",
        tenant_id=tenant.tenant_id,
        cell_id=dest,
        detail={"epoch": tenant.tenant_version, "mechanism": "dump_restore"},
    )
    return store.touch(tenant)
