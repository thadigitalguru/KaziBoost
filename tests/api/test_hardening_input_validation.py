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


def test_mpesa_rejects_non_kes_currency():
    headers = _auth_headers("hard1@example.com", "Validation Shop")
    response = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700123000", "amount": 1000, "currency": "USD", "reference": "INV-1"},
    )
    assert response.status_code == 400
    assert "KES" in response.json()["detail"]


def test_mpesa_rejects_non_kenyan_phone_format():
    headers = _auth_headers("hard2@example.com", "Validation Shop 2")
    response = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+15550001111", "amount": 1000, "currency": "KES", "reference": "INV-2"},
    )
    assert response.status_code == 400
    assert "+254" in response.json()["detail"]
