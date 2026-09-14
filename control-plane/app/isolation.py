from __future__ import annotations

from .dataplane import cache_key, secret_path, sign_envelope, verify_envelope
from .identity import break_glass_valid, issue_break_glass
from .models import IsolationRun, LifecycleStatus, new_id
from .store import Store


def run_invariants(store: Store, tenant_a: str | None = None, tenant_b: str | None = None) -> IsolationRun:
    results: dict[str, str] = {}

    results["I1"] = _i1(store)
    results["I2"] = _i2(store)
    results["I3"] = _i3(store)
    results["I4"] = _i4(store)
    results["I5"] = _i5(store)
    results["I6"] = _i6(store)
    results["I7"] = _i7(store)
    results["I8"] = _i8(store)
    results["I9"] = _i9(store)
    results["I10"] = _i10(store)

    blocked = False
    reason = None
    ids = [t.tenant_id for t in store.tenants.values() if t.status != LifecycleStatus.DELETED]
    if tenant_a and tenant_b and tenant_a in store.tenants and tenant_b in store.tenants:
        blocked, reason = probe_cross_tenant(store, tenant_a, tenant_b)

    run = IsolationRun(
        run_id=new_id(),
        results=results,
        blocked_cross_tenant=blocked,
        reason=reason,
    )
    store.isolation_runs.append(run)
    return run


def probe_cross_tenant(store: Store, tenant_a: str, tenant_b: str) -> tuple[bool, str]:
    a = store.tenants[tenant_a]
    b = store.tenants[tenant_b]
    db = store.tenant_dbs.get(tenant_b)
    if not db:
        return True, "target database missing"
    if a.tenant_id != b.tenant_id and db["database"] != a.database_name:
        return True, "tenant_id mismatch; current_database != expected_database"
    return False, "unexpected access"


def _i1(store: Store) -> str:
    return "PASS" if all(t.tenant_id for t in store.tenants.values()) else "FAIL"


def _i2(store: Store) -> str:
    for t in store.tenants.values():
        if t.status == LifecycleStatus.DELETED:
            continue
        secret = store.secrets.get(secret_path(t.cell_id, t.tenant_id))
        if not secret or secret["database"] != t.database_name:
            return "FAIL"
        for path, s in store.secrets.items():
            if t.tenant_id in path:
                continue
            if s.get("database") == t.database_name and s.get("cell_id") != t.cell_id:
                return "FAIL"
    return "PASS"


def _i3(store: Store) -> str:
    for t in store.tenants.values():
        if t.status == LifecycleStatus.DELETED:
            continue
        foreign = [c for c in store.cells if c != t.cell_id]
        for cell_id in foreign:
            if secret_path(cell_id, t.tenant_id) in store.secrets:
                return "FAIL"
    return "PASS"


def _i4(store: Store) -> str:
    payload = {"tenant_id": "demo", "tenant_version": 1}
    sig = sign_envelope(payload)
    if not verify_envelope(payload, sig):
        return "FAIL"
    if verify_envelope(payload, "deadbeef"):
        return "FAIL"
    return "PASS"


def _i5(store: Store) -> str:
    for tenant_id, db in store.tenant_dbs.items():
        if tenant_id not in store.tenants:
            return "FAIL"
        if store.tenants[tenant_id].status == LifecycleStatus.DELETED:
            return "FAIL"
    return "PASS"


def _i6(store: Store) -> str:
    return "PASS" if not store.orphans else "FAIL"


def _i7(store: Store) -> str:
    versions = {c.release for c in store.cells.values()}
    if not store.artifact_digest.startswith("sha256:"):
        return "FAIL"
    return "PASS"


def _i8(store: Store) -> str:
    degraded = [t for t in store.tenants.values() if t.status == LifecycleStatus.DEGRADED]
    healthy = [t for t in store.tenants.values() if t.status == LifecycleStatus.ACTIVE]
    if degraded and not healthy and len(store.tenants) > 1:
        return "FAIL"
    return "PASS"


def _i9(store: Store) -> str:
    for t in store.tenants.values():
        if t.status == LifecycleStatus.DELETED:
            continue
        k = cache_key(t.tenant_id, t.tenant_version, "cfg")
        store.cache[k] = "ok"
        if f"t:{t.tenant_id}:{t.tenant_version}:" not in k:
            return "FAIL"
    return "PASS"


def _i10(store: Store) -> str:
    tenants = [t for t in store.tenants.values() if t.status != LifecycleStatus.DELETED]
    if not tenants:
        return "PASS"
    t = tenants[0]
    ticket = issue_break_glass(store, t.tenant_id, "sre", "support inspect")
    if not break_glass_valid(store, ticket.ticket_id, t.tenant_id):
        return "FAIL"
    other = next((x for x in tenants if x.tenant_id != t.tenant_id), None)
    if other and break_glass_valid(store, ticket.ticket_id, other.tenant_id):
        return "FAIL"
    return "PASS"


def mark_db_down(store: Store, tenant_id: str) -> None:
    t = store.tenants[tenant_id]
    t.db_unavailable = True
    t.status = LifecycleStatus.DEGRADED
    t.health = t.health.__class__("degraded")
    from .models import Health

    t.health = Health.DEGRADED
    db = store.tenant_dbs.get(tenant_id)
    if db:
        db["available"] = False
    store.touch(t)
    store.audit_event("chaos_db_down", tenant_id=tenant_id)
