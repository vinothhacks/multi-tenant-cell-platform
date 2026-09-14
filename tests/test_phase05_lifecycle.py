def test_provision_state_machine_and_overflow(client):
    first = client.post("/v1/tenants", json={"name": "Acme Logistics"}).json()
    assert first["status"] == "active"
    assert first["lifecycle_step"] == "active"
    assert first["provisioning_seconds"] is not None
    assert first["provisioning_seconds"] < 900

    seeded = client.post("/v1/synthetic/seed", json={"count": 20, "prefix": "syn"}).json()
    assert len(seeded["created"]) == 20
    cells = {row["cell_id"] for row in client.get("/v1/tenants").json() if row["status"] != "deleted"}
    assert "cell-01" in cells
    assert "cell-02" in cells

    fleet = client.get("/v1/fleet").json()
    assert fleet["total_tenants"] >= 21


def test_suspend_and_offboard(client):
    t = client.post("/v1/tenants", json={"name": "TempCo"}).json()
    s = client.post(f"/v1/tenants/{t['tenant_id']}/suspend").json()
    assert s["status"] == "suspended"
    blocked = client.get("/dp/health", headers={"X-Tenant-Id": t["tenant_id"]})
    assert blocked.status_code == 403
    d = client.post(f"/v1/tenants/{t['tenant_id']}/delete").json()
    assert d["status"] == "deleted"
    tombstone = client.get(f"/v1/tenants/{t['tenant_id']}").json()
    assert tombstone["status"] == "deleted"
