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


def test_bot_replies_from_faq_knowledge_base():
    headers = _auth_headers("wabot1@example.com", "Amina Salon")

    client.post(
        "/v1/whatsapp/faq",
        headers=headers,
        json={"question": "What are your opening hours?", "answer": "We are open 8am to 8pm daily."},
    )

    incoming = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers=headers,
        json={"from_phone": "+254700666100", "message_text": "opening hours?", "language": "en"},
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

    incoming = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers=headers,
        json={"from_phone": "+254700666200", "message_text": "Can I get delivery to Rongai?", "language": "en"},
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
