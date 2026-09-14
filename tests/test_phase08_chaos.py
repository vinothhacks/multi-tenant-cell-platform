def test_invariants_and_cross_tenant_block(client):
    a = client.post("/v1/tenants", json={"name": "Alpha"}).json()
    b = client.post("/v1/tenants", json={"name": "Beta"}).json()
    run = client.post(
        "/v1/isolation/run",
        json={"tenant_a": a["tenant_id"], "tenant_b": b["tenant_id"]},
    ).json()
    for key in [f"I{i}" for i in range(1, 11)]:
        assert run["results"][key] == "PASS", key
    assert run["blocked_cross_tenant"] is True
    assert "tenant_id mismatch" in run["reason"]


def test_chaos_one_tenant_others_healthy(client):
    client.post("/v1/synthetic/seed", json={"count": 12, "prefix": "fleet"})
    tenants = [t for t in client.get("/v1/tenants").json() if t["status"] == "active"]
    victim = tenants[0]["tenant_id"]
    r = client.post("/v1/chaos/db-down", json={"tenant_id": victim}).json()
    assert r["degraded"] == victim
    assert r["others_healthy"] is True
    assert r["others"] >= 11
    victim_body = client.get(f"/v1/tenants/{victim}").json()
    assert victim_body["status"] == "degraded"
    down = client.get("/dp/health", headers={"X-Tenant-Id": victim})
    assert down.status_code == 503
