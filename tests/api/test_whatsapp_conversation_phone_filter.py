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


def _ingest(headers: dict[str, str], event_id: str, from_phone: str, message_text: str) -> None:
    payload = {"from_phone": from_phone, "message_text": message_text, "language": "en"}
    signature = build_whatsapp_signature(event_id=event_id, **payload)
    client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": event_id, "x-webhook-signature": signature},
        json=payload,
    )


def test_conversation_listing_can_filter_by_phone():
    headers = _auth_headers("waphone@example.com", "WA Phone Filter Shop")

    _ingest(headers, "evt-phone-1", "+254700555101", "Need pricing")
    _ingest(headers, "evt-phone-2", "+254700555102", "Need booking")

    response = client.get("/v1/whatsapp/conversations?from_phone=%2B254700555101", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["from_phone"] == "+254700555101"
