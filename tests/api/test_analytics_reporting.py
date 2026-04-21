from fastapi.testclient import TestClient

from kaziboost_api.main import app
from kaziboost_api.payments_security import build_mpesa_callback_signature
from kaziboost_api.whatsapp_security import build_whatsapp_signature


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


def test_dashboard_kpis_show_leads_conversations_and_sales():
    headers = _auth_headers("analytics1@example.com", "Amina Salon")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Lead Form", "kind": "lead", "fields": ["name", "email"]},
    ).json()

    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "Jane",
            "phone": "+254700999101",
            "email": "jane.analytics@example.com",
            "message": "Need booking",
            "source": "web_form",
            "tags": ["lead"],
        },
    )

    webhook_payload = {"from_phone": "+254700999102", "message_text": "Need pricing", "language": "en"}
    webhook_signature = build_whatsapp_signature(event_id="evt-analytics-1", **webhook_payload)
    client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": "evt-analytics-1", "x-webhook-signature": webhook_signature},
        json=webhook_payload,
    )

    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700999103", "amount": 5000, "currency": "KES", "reference": "SALE-1"},
    ).json()
    callback_payload = {"payment_id": payment["payment_id"], "provider_tx_id": "MP-TX-A1", "status": "success"}
    callback_sig = build_mpesa_callback_signature(**callback_payload)
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": callback_sig},
        json=callback_payload,
    )

    dashboard = client.get("/v1/analytics/dashboard", headers=headers)
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["kpis"]["total_leads"] >= 1
    assert body["kpis"]["open_conversations"] >= 1
    assert body["kpis"]["successful_payments"] >= 1


def test_reporting_export_and_schedule_summary():
    headers = _auth_headers("analytics2@example.com", "Kamau Hardware")

    export_csv = client.get("/v1/analytics/reports/export.csv", headers=headers)
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]
    assert "metric,value" in export_csv.text

    schedule = client.post(
        "/v1/analytics/reports/schedule",
        headers=headers,
        json={"email": "owner@kamauhardware.co.ke", "frequency": "weekly"},
    )

    assert schedule.status_code == 201
    assert schedule.json()["frequency"] == "weekly"
    assert schedule.json()["status"] == "scheduled"
