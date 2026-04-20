from fastapi.testclient import TestClient

from kaziboost_api.main import app


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


def test_mpesa_callback_is_idempotent_for_duplicate_events():
    headers = _auth_headers("paycb1@example.com", "Amina Salon")

    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={
            "phone": "+254700888111",
            "amount": 3200,
            "currency": "KES",
            "reference": "ORDER-103",
            "contact_id": "contact-103",
        },
    ).json()

    first = client.post(
        "/v1/payments/mpesa/callback",
        headers=headers,
        json={"payment_id": payment["payment_id"], "provider_tx_id": "MPESA-TX-1", "status": "success"},
    )
    duplicate = client.post(
        "/v1/payments/mpesa/callback",
        headers=headers,
        json={"payment_id": payment["payment_id"], "provider_tx_id": "MPESA-TX-1", "status": "success"},
    )

    assert first.status_code == 200
    assert first.json()["idempotent"] is False
    assert duplicate.status_code == 200
    assert duplicate.json()["idempotent"] is True

    fetched = client.get(f"/v1/payments/{payment['payment_id']}", headers=headers)
    assert fetched.json()["status"] == "success"


def test_reconciliation_lists_payments_for_contact():
    headers = _auth_headers("paycb2@example.com", "Kamau Hardware")

    created = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={
            "phone": "+254700888222",
            "amount": 2100,
            "currency": "KES",
            "reference": "ORDER-220",
            "contact_id": "contact-220",
        },
    ).json()

    client.post(
        "/v1/payments/mpesa/callback",
        headers=headers,
        json={"payment_id": created["payment_id"], "provider_tx_id": "MPESA-TX-2", "status": "success"},
    )

    reconciliation = client.get("/v1/payments/reconciliation?contact_id=contact-220", headers=headers)
    assert reconciliation.status_code == 200
    assert reconciliation.json()["total"] == 1
    assert reconciliation.json()["items"][0]["reference"] == "ORDER-220"
