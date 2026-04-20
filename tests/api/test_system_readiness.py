from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


def test_readiness_endpoint_reports_component_checks():
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["api"] == "ok"
    assert body["checks"]["storage"] == "ok"
