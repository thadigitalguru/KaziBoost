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


def test_reconciliation_filters_by_payment_status():
    headers = _auth_headers("precon@example.com", "Reconciliation Shop")

    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={
            "phone": "+254700333201",
            "amount": 1800,
            "currency": "KES",
            "reference": "RECON-1",
            "contact_id": "contact-1",
        },
    ).json()

    signature = build_mpesa_callback_signature(
        payment_id=payment["payment_id"],
        provider_tx_id="tx-recon-1",
        status="success",
    )
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": signature},
        json={"payment_id": payment["payment_id"], "provider_tx_id": "tx-recon-1", "status": "success"},
    )

    filtered = client.get("/v1/payments/reconciliation?contact_id=contact-1&status=success", headers=headers)
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["status"] == "success"

    empty = client.get("/v1/payments/reconciliation?contact_id=contact-1&status=pending", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["total"] == 0
