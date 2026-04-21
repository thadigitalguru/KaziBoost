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


def test_failed_payments_can_filter_by_reason():
    headers = _auth_headers("pfreason@example.com", "Failure Reason Shop")

    p1 = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700777801", "amount": 1000, "currency": "KES", "reference": "FAIL-1"},
    ).json()
    p2 = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700777802", "amount": 1200, "currency": "KES", "reference": "FAIL-2"},
    ).json()

    sig1 = build_mpesa_callback_signature(payment_id=p1["payment_id"], provider_tx_id="tx-f1", status="failed")
    sig2 = build_mpesa_callback_signature(payment_id=p2["payment_id"], provider_tx_id="tx-f2", status="failed")
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": sig1},
        json={"payment_id": p1["payment_id"], "provider_tx_id": "tx-f1", "status": "failed", "reason": "insufficient_funds"},
    )
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": sig2},
        json={"payment_id": p2["payment_id"], "provider_tx_id": "tx-f2", "status": "failed", "reason": "timeout"},
    )

    response = client.get("/v1/payments/failures?reason=insufficient_funds", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["reason"] == "insufficient_funds"
