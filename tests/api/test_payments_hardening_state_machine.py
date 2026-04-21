from fastapi.testclient import TestClient

from kaziboost_api.main import app
from kaziboost_api.payments_security import build_mpesa_callback_signature


client = TestClient(app)


def _auth_headers(email: str, business_name: str) -> dict[str, str]:
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


def test_callback_rejects_invalid_signature():
    headers = _auth_headers("payhard1@example.com", "Amina Salon")

    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700100100", "amount": 1500, "currency": "KES", "reference": "INV-H1"},
    ).json()

    response = client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": "invalid"},
        json={"payment_id": payment["payment_id"], "provider_tx_id": "TX-H1", "status": "success"},
    )

    assert response.status_code == 401


def test_callback_rejects_invalid_state_transition():
    headers = _auth_headers("payhard2@example.com", "Kamau Hardware")

    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700200200", "amount": 2500, "currency": "KES", "reference": "INV-H2"},
    ).json()

    payload_success = {"payment_id": payment["payment_id"], "provider_tx_id": "TX-H2", "status": "success"}
    sig_success = build_mpesa_callback_signature(**payload_success)
    first = client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": sig_success},
        json=payload_success,
    )
    assert first.status_code == 200

    payload_failed = {"payment_id": payment["payment_id"], "provider_tx_id": "TX-H3", "status": "failed"}
    sig_failed = build_mpesa_callback_signature(**payload_failed)
    second = client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": sig_failed},
        json=payload_failed,
    )

    assert second.status_code == 400
    assert "Invalid payment state transition" in second.json()["detail"]
