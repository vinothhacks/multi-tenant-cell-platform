def test_move_acme_between_cells(client):
    a = client.post("/v1/tenants", json={"name": "Acme"}).json()
    client.post("/v1/synthetic/seed", json={"count": 8, "prefix": "fill"})
    source = a["cell_id"]
    moved = client.post(
        f"/v1/tenants/{a['tenant_id']}/move",
        json={"reason": "cell capacity / noisy neighbour"},
    ).json()
    assert moved["move_committed"] is True
    assert moved["cell_id"] != source
    assert moved["tenant_version"] == a["tenant_version"] + 1
    assert moved["move_gates"]["routing_switched"] is True
    assert moved["move_gates"]["epoch_increment"] is True


def test_abort_before_commit_keeps_source(client):
    a = client.post("/v1/tenants", json={"name": "Stay"}).json()
    client.post("/v1/tenants", json={"name": "Other"})
    r = client.post(
        f"/v1/tenants/{a['tenant_id']}/move",
        json={"target_cell_id": "cell-02", "abort_before_commit": True},
    ).json()
    assert r["cell_id"] == a["cell_id"]
    assert r["move_committed"] is False
    assert r["tenant_version"] == a["tenant_version"]


def test_crash_before_commit_source_authoritative(client):
    a = client.post("/v1/tenants", json={"name": "CrashMove"}).json()
    r = client.post(
        f"/v1/tenants/{a['tenant_id']}/move",
        json={"target_cell_id": "cell-02", "crash_before_commit": True},
    ).json()
    assert r["cell_id"] == a["cell_id"]
    assert r["move_committed"] is False
