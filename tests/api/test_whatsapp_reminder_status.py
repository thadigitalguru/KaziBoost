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


def test_reminder_can_be_marked_sent_and_filtered():
    headers = _auth_headers("remsent@example.com", "Reminder Sent Shop")

    payload = {"from_phone": "+254700888201", "message_text": "Need update", "language": "en"}
    sig = build_whatsapp_signature(event_id="evt-remsent-1", **payload)
    convo = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": "evt-remsent-1", "x-webhook-signature": sig},
        json=payload,
    ).json()

    reminder = client.post(
        f"/v1/whatsapp/conversations/{convo['thread_id']}/remind",
        headers=headers,
        json={"message": "Checking in."},
    ).json()

    sent = client.patch(f"/v1/whatsapp/reminders/{reminder['id']}/sent", headers=headers)
    assert sent.status_code == 200
    assert sent.json()["status"] == "sent"

    filtered = client.get("/v1/whatsapp/reminders/history?status=sent", headers=headers)
    assert filtered.status_code == 200
    assert filtered.json()["total"] >= 1
    assert all(x["status"] == "sent" for x in filtered.json()["items"])
