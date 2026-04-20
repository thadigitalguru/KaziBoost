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


def test_mpesa_initiate_creates_pending_payment():
    headers = _auth_headers("pay1@example.com", "Amina Salon")

    initiated = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={
            "phone": "+254700777111",
            "amount": 1500,
            "currency": "KES",
            "reference": "BOOKING-001",
        },
    )

    assert initiated.status_code == 201
    body = initiated.json()
    assert body["status"] == "pending"
    assert body["payment_id"]
    assert body["provider"] == "mpesa"

    fetched = client.get(f"/v1/payments/{body['payment_id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["reference"] == "BOOKING-001"


def test_payment_is_tenant_isolated():
    headers_1 = _auth_headers("pay2@example.com", "Kamau Hardware")
    headers_2 = _auth_headers("pay3@example.com", "Westlands Vet")

    initiated = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers_1,
        json={
            "phone": "+254700777222",
            "amount": 2500,
            "currency": "KES",
            "reference": "ORDER-002",
        },
    ).json()

    denied = client.get(f"/v1/payments/{initiated['payment_id']}", headers=headers_2)
    assert denied.status_code == 404
