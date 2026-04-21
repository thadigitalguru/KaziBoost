from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


def test_metrics_endpoint_exposes_core_counters():
    signup_payload = {
        "business_name": "Metrics Shop",
        "owner_name": "Owner",
        "email": "metrics@example.com",
        "password": "StrongPass123!",
    }
    client.post("/v1/auth/signup", json=signup_payload)
    login = client.post(
        "/v1/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    ).json()

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    body = metrics.text
    assert "kaziboost_auth_logins_total" in body
    assert "kaziboost_whatsapp_events_total" in body
    assert "kaziboost_payments_callbacks_total" in body

    assert login["access_token"]
