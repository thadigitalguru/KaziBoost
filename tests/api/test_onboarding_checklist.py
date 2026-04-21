from fastapi.testclient import TestClient

from kaziboost_api.main import app
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


def test_onboarding_checklist_reports_progress():
    headers = _auth_headers("onboard1@example.com", "Onboard Shop")

    site = client.post(
        "/v1/sites",
        headers=headers,
        json={"name": "Onboard Shop", "template_key": "salon-modern", "primary_language": "en"},
    ).json()
    client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={"slug": "home", "title": "Home", "language": "en", "body_blocks": ["hero"]},
    )
    client.post(f"/v1/sites/{site['id']}/publish", headers=headers)

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
            "phone": "+254700900900",
            "email": "jane@onboard.example",
            "message": "Need help",
            "source": "web_form",
            "tags": ["lead"],
        },
    )

    wa_payload = {"from_phone": "+254700900901", "message_text": "Hi", "language": "en"}
    wa_sig = build_whatsapp_signature(event_id="evt-onboard-1", **wa_payload)
    client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": "evt-onboard-1", "x-webhook-signature": wa_sig},
        json=wa_payload,
    )

    checklist = client.get("/v1/onboarding/checklist", headers=headers)
    assert checklist.status_code == 200
    body = checklist.json()
    assert body["completed"] >= 3
    assert body["items"]["site_published"] is True
    assert body["items"]["first_lead_captured"] is True
    assert body["items"]["whatsapp_connected"] is True
