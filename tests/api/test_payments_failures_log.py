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


def test_failed_payment_callbacks_are_logged_with_reason():
    headers = _auth_headers("pfail@example.com", "Payment Failure Shop")

    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700821001", "amount": 1800, "currency": "KES", "reference": "FAIL-1"},
    ).json()

    cb_payload = {
        "payment_id": payment["payment_id"],
        "provider_tx_id": "FAIL-TX-1",
        "status": "failed",
        "reason": "insufficient_funds",
    }
    cb_sig = build_mpesa_callback_signature(
        payment_id=cb_payload["payment_id"],
        provider_tx_id=cb_payload["provider_tx_id"],
        status=cb_payload["status"],
    )
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": cb_sig},
        json=cb_payload,
    )

    failures = client.get("/v1/payments/failures", headers=headers)
    assert failures.status_code == 200
    assert failures.json()["total"] >= 1
    assert failures.json()["items"][0]["reason"] == "insufficient_funds"
