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


def _incoming(headers: dict[str, str], event_id: str, phone: str) -> str:
    payload = {"from_phone": phone, "message_text": "Hello", "language": "en"}
    sig = build_whatsapp_signature(event_id=event_id, **payload)
    return client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": event_id, "x-webhook-signature": sig},
        json=payload,
    ).json()["thread_id"]


def test_reminder_history_can_filter_by_thread_id():
    headers = _auth_headers("remthread@example.com", "Reminder Thread Shop")

    thread_a = _incoming(headers, "evt-remthread-a", "+254700500201")
    thread_b = _incoming(headers, "evt-remthread-b", "+254700500202")

    client.post(f"/v1/whatsapp/conversations/{thread_a}/remind", headers=headers, json={"message": "Ping A"})
    client.post(f"/v1/whatsapp/conversations/{thread_b}/remind", headers=headers, json={"message": "Ping B"})

    response = client.get(f"/v1/whatsapp/reminders/history?thread_id={thread_a}", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["thread_id"] == thread_a
