def test_one_cell_and_tenant_db(client):
    r = client.post("/v1/tenants", json={"name": "CellOne"})
    t = r.json()
    assert t["cell_id"] == "cell-01"
    assert t["database_name"].startswith("db_")
    ready = client.get("/dp/health", headers={"X-Tenant-Id": t["tenant_id"]})
    assert ready.status_code == 200
    assert ready.json()["database"] == t["database_name"]


def test_missing_tenant_rejected(client):
    r = client.get("/dp/health")
    assert r.status_code == 400
