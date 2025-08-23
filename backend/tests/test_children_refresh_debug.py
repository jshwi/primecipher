def test_healthz(app_client):
    r = app_client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ok") is True

def test_narratives_24h_again(app_client):
    r = app_client.get("/narratives?source=file&window=24h")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert isinstance(data.get("narratives", []), list)

