from app.models import IsolationClass, SizeClass
from app.placement import place
from app.store import Store


def test_registry_fields(client):
    r = client.post(
        "/v1/tenants",
        json={"name": "Acme Logistics", "isolation": "L1", "size_class": "S", "region": "Chennai"},
    )
    assert r.status_code == 201
    body = r.json()
    for key in (
        "tenant_id",
        "slug",
        "isolation",
        "tier",
        "cell_id",
        "database_name",
        "schema_version",
        "tenant_version",
        "status",
        "flags",
    ):
        assert key in body
    assert body["status"] == "active"
    assert body["tier"] == "pooled"
    listed = client.get("/v1/tenants").json()
    assert len(listed) == 1
    fleet = client.get("/v1/fleet").json()
    assert fleet["total_tenants"] == 1


def test_placement_policy_outputs():
    store = Store()
    tier, cell = place(store, isolation=IsolationClass.L1, size=SizeClass.S, region="Chennai", name="a")
    assert tier.value == "pooled"
    assert cell.kind == "pooled"

    tier, cell = place(store, isolation=IsolationClass.L2, size=SizeClass.S, region="Chennai", name="b")
    assert tier.value == "dedicated"
    assert cell.kind == "dedicated"

    tier, cell = place(store, isolation=IsolationClass.L1, size=SizeClass.XL, region="Chennai", name="c")
    assert tier.value == "dedicated"

    tier, cell = place(store, isolation=IsolationClass.L3, size=SizeClass.S, region="eu", name="d")
    assert tier.value == "sovereign"


def test_invalid_isolation_rejected(client):
    r = client.post("/v1/tenants", json={"name": "x", "isolation": "L9"})
    assert r.status_code == 422
