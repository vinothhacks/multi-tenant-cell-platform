from __future__ import annotations

from .dataplane import create_tenant_db, drop_tenant_db, persist_db_file
from .models import (
    PROVISION_STEPS,
    Health,
    LifecycleStatus,
    Tenant,
    utcnow,
)
from .store import Store


class CrashInjected(Exception):
    """Controller stopped after a completed step so a test can resume."""


def _step_name(status: LifecycleStatus) -> str:
    return status.value


def reconcile_provision(store: Store, tenant: Tenant, data_dir=None) -> Tenant:
    if tenant.status in {
        LifecycleStatus.ACTIVE,
        LifecycleStatus.SUSPENDED,
        LifecycleStatus.DELETED,
        LifecycleStatus.DEGRADED,
        LifecycleStatus.RETENTION_HOLD,
    }:
        return tenant

    if tenant.status in {LifecycleStatus.FAILED_TERMINAL}:
        return tenant

    if tenant.status == LifecycleStatus.FAILED:
        tenant.status = LifecycleStatus.REQUESTED

    completed = set(tenant.completed_steps)
    for step in PROVISION_STEPS:
        name = _step_name(step)
        if name in completed:
            continue
        tenant.status = step
        tenant.lifecycle_step = name
        _apply_step(store, tenant, step)
        tenant.completed_steps.append(name)
        store.touch(tenant)
        store.audit_event("lifecycle_step", tenant_id=tenant.tenant_id, detail={"step": name})
        if tenant.crash_after == name:
            raise CrashInjected(name)

    tenant.status = LifecycleStatus.ACTIVE
    tenant.health = Health.HEALTHY
    tenant.provisioned_at = tenant.provisioned_at or utcnow()
    if data_dir:
        persist_db_file(data_dir, tenant, store)
    return store.touch(tenant)


def _apply_step(store: Store, tenant: Tenant, step: LifecycleStatus) -> None:
    if step == LifecycleStatus.DATABASE_READY:
        create_tenant_db(store, tenant)
    elif step == LifecycleStatus.SCHEMA_READY:
        db = store.tenant_dbs[tenant.tenant_id]
        db["schema_version"] = tenant.schema_version
        db["tables"] = ["events"]
    elif step == LifecycleStatus.SECRETS_READY:
        tenant.secret_version = max(tenant.secret_version, 1)
    elif step == LifecycleStatus.ROUTING_READY:
        store.cache[f"route:{tenant.slug}"] = {
            "tenant_id": tenant.tenant_id,
            "cell_id": tenant.cell_id,
            "tenant_version": tenant.tenant_version,
        }
    elif step == LifecycleStatus.ACTIVE:
        tenant.health = Health.HEALTHY


def suspend(store: Store, tenant: Tenant) -> Tenant:
    if tenant.status == LifecycleStatus.DELETED:
        raise ValueError("deleted")
    tenant.status = LifecycleStatus.SUSPENDED
    tenant.health = Health.DEGRADED
    store.audit_event("suspend", tenant_id=tenant.tenant_id)
    return store.touch(tenant)


def resume(store: Store, tenant: Tenant) -> Tenant:
    if tenant.status != LifecycleStatus.SUSPENDED:
        raise ValueError("not suspended")
    tenant.status = LifecycleStatus.ACTIVE
    tenant.health = Health.HEALTHY
    store.audit_event("resume", tenant_id=tenant.tenant_id)
    return store.touch(tenant)


def offboard(store: Store, tenant: Tenant) -> Tenant:
    if tenant.legal_hold:
        tenant.status = LifecycleStatus.RETENTION_HOLD
        store.audit_event("legal_hold", tenant_id=tenant.tenant_id)
        return store.touch(tenant)
    tenant.status = LifecycleStatus.DELETING
    drop_tenant_db(store, tenant)
    store.cache.pop(f"route:{tenant.slug}", None)
    for key in list(store.cache):
        if key.startswith(f"t:{tenant.tenant_id}:"):
            store.cache.pop(key, None)
    tenant.status = LifecycleStatus.DELETED
    tenant.health = Health.DOWN
    store.audit_event("deleted", tenant_id=tenant.tenant_id, detail={"tombstone": True})
    return store.touch(tenant)
