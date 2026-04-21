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


def test_whatsapp_overdue_queue_lists_unassigned_open_threads():
    headers = _auth_headers("waoverdue@example.com", "WA Overdue Shop")
    payload = {"from_phone": "+254700731001", "message_text": "Need quote", "language": "en"}
    sig = build_whatsapp_signature(event_id="evt-overdue-1", **payload)

    created = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": "evt-overdue-1", "x-webhook-signature": sig},
        json=payload,
    )
    assert created.status_code in (200, 201)

    queue = client.get("/v1/whatsapp/queue/overdue", headers=headers)
    assert queue.status_code == 200
    assert queue.json()["total"] >= 1
    assert queue.json()["items"][0]["thread_id"] == created.json()["thread_id"]
