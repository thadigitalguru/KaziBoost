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


def _webhook_headers(auth_headers: dict[str, str], event_id: str, payload: dict) -> dict[str, str]:
    signature = build_whatsapp_signature(
        event_id=event_id,
        from_phone=payload["from_phone"],
        message_text=payload["message_text"],
        language=payload["language"],
    )
    return {**auth_headers, "x-event-id": event_id, "x-webhook-signature": signature}


def test_bot_replies_from_faq_knowledge_base():
    headers = _auth_headers("wabot1@example.com", "Amina Salon")

    client.post(
        "/v1/whatsapp/faq",
        headers=headers,
        json={"question": "What are your opening hours?", "answer": "We are open 8am to 8pm daily."},
    )

    incoming_payload = {"from_phone": "+254700666100", "message_text": "opening hours?", "language": "en"}
    incoming = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers=_webhook_headers(headers, "evt-bot-1", incoming_payload),
        json=incoming_payload,
    ).json()

    bot = client.post(
        f"/v1/whatsapp/conversations/{incoming['thread_id']}/reply-bot",
        headers=headers,
    )

    assert bot.status_code == 200
    body = bot.json()
    assert body["mode"] == "bot"
    assert "8am to 8pm" in body["reply_text"]


def test_unknown_question_triggers_handoff_and_assignment():
    headers = _auth_headers("wabot2@example.com", "Kamau Hardware")

    incoming_payload = {"from_phone": "+254700666200", "message_text": "Can I get delivery to Rongai?", "language": "en"}
    incoming = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers=_webhook_headers(headers, "evt-bot-2", incoming_payload),
        json=incoming_payload,
    ).json()

    bot = client.post(
        f"/v1/whatsapp/conversations/{incoming['thread_id']}/reply-bot",
        headers=headers,
    )
    assert bot.status_code == 200
    assert bot.json()["mode"] == "handoff_required"

    handoff = client.post(
        f"/v1/whatsapp/conversations/{incoming['thread_id']}/handoff",
        headers=headers,
        json={"assigned_to": "support-agent-1"},
    )

    assert handoff.status_code == 200
    assert handoff.json()["status"] == "handoff"
    assert handoff.json()["assigned_to"] == "support-agent-1"
