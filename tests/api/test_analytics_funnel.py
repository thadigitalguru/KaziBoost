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


def test_funnel_metrics_include_conversion_rates():
    headers = _auth_headers("funnel@example.com", "Funnel Shop")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Lead Form", "kind": "lead", "fields": ["name", "email"]},
    ).json()
    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "Lead",
            "phone": "+254700801001",
            "email": "lead@funnel.example",
            "message": "Need quote",
            "source": "web_form",
            "tags": ["lead"],
        },
    )

    wa_payload = {"from_phone": "+254700801002", "message_text": "Need pricing", "language": "en"}
    wa_sig = build_whatsapp_signature(event_id="evt-funnel-1", **wa_payload)
    client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": "evt-funnel-1", "x-webhook-signature": wa_sig},
        json=wa_payload,
    )

    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700801003", "amount": 3500, "currency": "KES", "reference": "FUN-1"},
    ).json()
    cb_payload = {"payment_id": payment["payment_id"], "provider_tx_id": "FUN-TX-1", "status": "success"}
    cb_sig = build_mpesa_callback_signature(**cb_payload)
    client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": cb_sig},
        json=cb_payload,
    )

    funnel = client.get("/v1/analytics/funnel", headers=headers)
    assert funnel.status_code == 200
    body = funnel.json()
    assert body["stages"]["leads"] >= 1
    assert body["stages"]["conversations"] >= 1
    assert body["stages"]["successful_payments"] >= 1
    assert "lead_to_payment_rate" in body["conversion"]
