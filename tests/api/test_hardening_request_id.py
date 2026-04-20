from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


def test_request_id_is_generated_when_missing():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-request-id")


def test_request_id_is_preserved_when_provided():
    response = client.get("/health", headers={"x-request-id": "req-12345"})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "req-12345"
