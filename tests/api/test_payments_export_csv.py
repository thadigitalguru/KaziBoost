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


def test_payments_export_csv_contains_rows():
    headers = _auth_headers("pexport@example.com", "Payments Export Shop")

    client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700833001", "amount": 2200, "currency": "KES", "reference": "EXP-1"},
    )

    export = client.get("/v1/payments/export.csv", headers=headers)
    assert export.status_code == 200
    assert "text/csv" in export.headers["content-type"]
    assert "payment_id" in export.text
    assert "EXP-1" in export.text
