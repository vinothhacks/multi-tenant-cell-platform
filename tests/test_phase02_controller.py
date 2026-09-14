from app.controller import CrashInjected, reconcile_provision
from app.main import create_tenant_record
from app.models import TenantCreate


def test_crash_mid_provision_resumes(store):
    t = create_tenant_record(store, TenantCreate(name="ResumeMe", crash_after="database_ready"))
    try:
        reconcile_provision(store, t)
        raise AssertionError("expected crash")
    except CrashInjected as e:
        assert str(e) == "database_ready"
    assert "database_ready" in t.completed_steps
    assert t.tenant_id in store.tenant_dbs
    t.crash_after = None
    reconcile_provision(store, t)
    assert t.status.value == "active"
    assert t.completed_steps.count("database_ready") == 1


def test_retry_does_not_duplicate_db(store):
    t = create_tenant_record(store, TenantCreate(name="Once"))
    reconcile_provision(store, t)
    db = store.tenant_dbs[t.tenant_id]
    reconcile_provision(store, t)
    assert store.tenant_dbs[t.tenant_id] is db
