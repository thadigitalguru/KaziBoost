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


def test_successful_payment_can_be_refunded_and_listed():
    headers = _auth_headers("refund1@example.com", "Refund Shop")
    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700701001", "amount": 4000, "currency": "KES", "reference": "REF-1"},
    ).json()

    cb_payload = {"payment_id": payment["payment_id"], "provider_tx_id": "REF-TX-1", "status": "success"}
    cb_sig = build_mpesa_callback_signature(**cb_payload)
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": cb_sig},
        json=cb_payload,
    )

    refund = client.post(
        f"/v1/payments/{payment['payment_id']}/refund",
        headers=headers,
        json={"amount": 1500, "reason": "customer_cancelled"},
    )
    assert refund.status_code == 201
    assert refund.json()["status"] == "refunded"

    listing = client.get(f"/v1/payments/{payment['payment_id']}/refunds", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


def test_pending_payment_cannot_be_refunded():
    headers = _auth_headers("refund2@example.com", "Refund Shop 2")
    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700701002", "amount": 2000, "currency": "KES", "reference": "REF-2"},
    ).json()

    denied = client.post(
        f"/v1/payments/{payment['payment_id']}/refund",
        headers=headers,
        json={"amount": 500, "reason": "manual_request"},
    )
    assert denied.status_code == 400
