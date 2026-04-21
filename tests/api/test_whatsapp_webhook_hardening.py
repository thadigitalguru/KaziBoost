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


def test_whatsapp_incoming_rejects_invalid_signature():
    headers = _auth_headers("wahard1@example.com", "Amina Salon")

    response = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": "evt-1", "x-webhook-signature": "bad-signature"},
        json={"from_phone": "+254700123123", "message_text": "Hi", "language": "en"},
    )

    assert response.status_code == 401


def test_whatsapp_incoming_is_idempotent_for_duplicate_event_id():
    headers = _auth_headers("wahard2@example.com", "Kamau Hardware")
    payload = {"from_phone": "+254700999888", "message_text": "Need pricing", "language": "en"}
    event_id = "evt-duplicate-1"
    signature = build_whatsapp_signature(event_id=event_id, **payload)

    first = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": event_id, "x-webhook-signature": signature},
        json=payload,
    )
    second = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": event_id, "x-webhook-signature": signature},
        json=payload,
    )

    assert first.status_code == 201
    assert first.json()["idempotent"] is False
    assert second.status_code == 200
    assert second.json()["idempotent"] is True
    assert first.json()["thread_id"] == second.json()["thread_id"]

    listing = client.get("/v1/whatsapp/conversations", headers=headers).json()
    assert listing["total"] == 1
