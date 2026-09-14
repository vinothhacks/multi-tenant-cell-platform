def test_economics_is_labelled_simulation(client):
    r = client.get("/v1/economics").json()
    assert "Simulation" in r["label"]
    assert r["rows"][0]["n"] == 20


def test_fleet_payload_has_console_fields(client):
    client.post("/v1/tenants", json={"name": "UiCo"})
    fleet = client.get("/v1/fleet").json()
    assert "tenants" in fleet
    assert "fleet_release" in fleet
    cells = client.get("/v1/cells").json()
    assert cells
