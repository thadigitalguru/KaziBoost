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


def test_whatsapp_reminder_creation_and_history():
    headers = _auth_headers("waremind@example.com", "WA Reminder Shop")
    payload = {"from_phone": "+254700881001", "message_text": "Need appointment", "language": "en"}
    sig = build_whatsapp_signature(event_id="evt-rem-1", **payload)
    convo = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": "evt-rem-1", "x-webhook-signature": sig},
        json=payload,
    ).json()

    reminder = client.post(
        f"/v1/whatsapp/conversations/{convo['thread_id']}/remind",
        headers=headers,
        json={"message": "Just checking in, do you still need help?"},
    )

    assert reminder.status_code == 201
    assert reminder.json()["status"] == "scheduled"

    history = client.get("/v1/whatsapp/reminders/history", headers=headers)
    assert history.status_code == 200
    assert history.json()["total"] >= 1
