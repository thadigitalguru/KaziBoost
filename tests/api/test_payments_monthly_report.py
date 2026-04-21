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


def test_monthly_report_returns_success_revenue_totals():
    headers = _auth_headers("pmonth@example.com", "Monthly Report Shop")

    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700741001", "amount": 6200, "currency": "KES", "reference": "MR-1"},
    ).json()

    cb_payload = {"payment_id": payment["payment_id"], "provider_tx_id": "MR-TX-1", "status": "success"}
    cb_sig = build_mpesa_callback_signature(**cb_payload)
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": cb_sig},
        json=cb_payload,
    )

    report = client.get("/v1/payments/reports/monthly", headers=headers)
    assert report.status_code == 200
    assert report.json()["month"]
    assert report.json()["successful_revenue"] >= 6200
    assert report.json()["successful_count"] >= 1
