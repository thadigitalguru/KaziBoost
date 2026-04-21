from fastapi.testclient import TestClient

from kaziboost_api.main import app
from kaziboost_api.payments_security import build_mpesa_callback_signature


client = TestClient(app)


def _signup_and_login(email: str, business_name: str) -> dict:
    signup_payload = {
        "business_name": business_name,
        "owner_name": "Owner",
        "email": email,
        "password": "StrongPass123!",
    }
    client.post("/v1/auth/signup", json=signup_payload)
    login = client.post(
        "/v1/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    ).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def test_audit_events_include_security_sensitive_actions():
    headers = _signup_and_login("audit1@example.com", "Audit Shop")

    teammate = client.post(
        "/v1/auth/teammates",
        headers=headers,
        json={"owner_name": "Marketer", "email": "aud-marketer@example.com", "password": "StrongPass123!", "role": "marketer"},
    ).json()

    client.patch(
        f"/v1/auth/users/{teammate['user']['id']}/role",
        headers=headers,
        json={"role": "manager"},
    )

    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700101010", "amount": 1000, "currency": "KES", "reference": "AUD-1"},
    ).json()

    callback_payload = {"payment_id": payment["payment_id"], "provider_tx_id": "AUD-TX-1", "status": "success"}
    callback_sig = build_mpesa_callback_signature(**callback_payload)
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": callback_sig},
        json=callback_payload,
    )

    events = client.get("/v1/audit/events", headers=headers)
    assert events.status_code == 200
    body = events.json()
    assert body["total"] >= 3
    event_types = {item["event_type"] for item in body["items"]}
    assert "teammate.created" in event_types
    assert "user.role.updated" in event_types
    assert "payment.callback.applied" in event_types
