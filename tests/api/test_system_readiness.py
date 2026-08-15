from fastapi.testclient import TestClient

from kaziboost_api.main import app, store


client = TestClient(app)


def test_readiness_endpoint_reports_component_checks():
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["api"] == "ok"
    assert body["checks"]["storage"] == "ok"
    assert body["checks"]["mpesa_webhook_secret"] == "local-default"
    assert body["checks"]["whatsapp_webhook_secret"] == "local-default"


def test_readiness_endpoint_reports_storage_errors(monkeypatch):
    monkeypatch.setattr(store, "storage_ready", lambda: False)

    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["storage"] == "error"
