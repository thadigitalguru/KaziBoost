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


def test_reconciliation_can_filter_by_provider_tx_id():
    headers = _auth_headers("recontx@example.com", "Reconciliation Tx Shop")

    p1 = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700444801", "amount": 3000, "currency": "KES", "reference": "REC-TX-1", "contact_id": "contact-xyz"},
    ).json()
    p2 = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700444802", "amount": 3500, "currency": "KES", "reference": "REC-TX-2", "contact_id": "contact-xyz"},
    ).json()

    sig1 = build_mpesa_callback_signature(payment_id=p1["payment_id"], provider_tx_id="tx-abc", status="success")
    sig2 = build_mpesa_callback_signature(payment_id=p2["payment_id"], provider_tx_id="tx-def", status="success")
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": sig1},
        json={"payment_id": p1["payment_id"], "provider_tx_id": "tx-abc", "status": "success"},
    )
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": sig2},
        json={"payment_id": p2["payment_id"], "provider_tx_id": "tx-def", "status": "success"},
    )

    response = client.get(
        "/v1/payments/reconciliation?contact_id=contact-xyz&provider_tx_id=tx-def",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["provider_tx_id"] == "tx-def"
