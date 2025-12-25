from jesse.app import create_app


def test_health():
    app = create_app()
    client = app.test_client()
    r = client.get("/api/health")
    assert r.status_code == 200


def test_greeting_requires_client_id():
    app = create_app()
    client = app.test_client()
    r = client.get("/api/greeting")
    assert r.status_code == 400


def test_greeting_ok():
    app = create_app()
    client = app.test_client()
    r = client.get("/api/greeting?client_id=oceanbite_001")
    assert r.status_code == 200
    data = r.get_json()
    assert "reply" in data
