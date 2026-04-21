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


def test_refund_report_groups_counts_by_reason():
    headers = _auth_headers("prefundreport@example.com", "Refund Report Shop")

    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700771001", "amount": 3000, "currency": "KES", "reference": "RR-1"},
    ).json()

    cb_payload = {"payment_id": payment["payment_id"], "provider_tx_id": "RR-TX-1", "status": "success"}
    cb_sig = build_mpesa_callback_signature(**cb_payload)
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": cb_sig},
        json=cb_payload,
    )

    client.post(
        f"/v1/payments/{payment['payment_id']}/refund",
        headers=headers,
        json={"amount": 1000, "reason": "customer_cancelled"},
    )

    report = client.get("/v1/payments/reports/refunds", headers=headers)
    assert report.status_code == 200
    assert report.json()["total_refunds"] >= 1
    assert report.json()["by_reason"]["customer_cancelled"]["count"] >= 1
