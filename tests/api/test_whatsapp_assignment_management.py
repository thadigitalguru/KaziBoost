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


def test_reassign_conversation_and_filter_by_assigned_agent():
    headers = _auth_headers("waassign@example.com", "WA Assign Shop")

    payload = {"from_phone": "+254700812001", "message_text": "Need response", "language": "en"}
    sig = build_whatsapp_signature(event_id="evt-assign-1", **payload)
    convo = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": "evt-assign-1", "x-webhook-signature": sig},
        json=payload,
    ).json()

    client.post(
        f"/v1/whatsapp/conversations/{convo['thread_id']}/handoff",
        headers=headers,
        json={"assigned_to": "agent-1"},
    )

    reassign = client.patch(
        f"/v1/whatsapp/conversations/{convo['thread_id']}/assign",
        headers=headers,
        json={"assigned_to": "agent-2"},
    )
    assert reassign.status_code == 200
    assert reassign.json()["assigned_to"] == "agent-2"

    queue = client.get("/v1/whatsapp/conversations?assigned_to=agent-2", headers=headers)
    assert queue.status_code == 200
    assert queue.json()["total"] == 1
