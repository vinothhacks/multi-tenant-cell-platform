def test_wave_release_and_isolated_failure(client):
    client.post("/v1/synthetic/seed", json={"count": 10, "prefix": "rel"})
    tenants = client.get("/v1/tenants").json()
    victim = tenants[0]["tenant_id"]
    # mark inject via recreate is hard; patch through chaos-like flag using store via failed tenant
    # Use dedicated inject on create:
    bad = client.post(
        "/v1/tenants",
        json={"name": "BadMigrate", "inject_migration_failure": True},
    ).json()
    rel = client.post("/v1/releases", json={"version": "V8"}).json()
    assert rel["digest"].startswith("sha256:")
    assert rel["wave"] == "canary"
    cont = client.post(f"/v1/releases/{rel['release_id']}/continue").json()
    fleet = client.post(f"/v1/releases/{rel['release_id']}/continue").json()
    assert fleet["status"] in {"complete", "halted", "in_progress"}
    bad_after = client.get(f"/v1/tenants/{bad['tenant_id']}").json()
    assert bad_after["status"] == "degraded"
    others = [
        t
        for t in client.get("/v1/tenants").json()
        if t["tenant_id"] != bad["tenant_id"] and t["status"] == "active"
    ]
    assert others
    healthy_on_v8 = [t for t in others if t["schema_version"] == "V8"]
    assert healthy_on_v8


def test_orchestrator_resume(client):
    client.post("/v1/synthetic/seed", json={"count": 4, "prefix": "rs"})
    rel = client.post("/v1/releases", json={"version": "V8"}).json()
    resumed = client.post(f"/v1/releases/{rel['release_id']}/resume").json()
    assert resumed["release_id"] == rel["release_id"]
