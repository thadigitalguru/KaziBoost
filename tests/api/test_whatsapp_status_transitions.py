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


def test_conversation_can_be_closed_and_reopened_and_filtered_by_status():
    headers = _auth_headers("wastatus@example.com", "WA Status Shop")
    payload = {"from_phone": "+254700601001", "message_text": "Hello", "language": "en"}
    signature = build_whatsapp_signature(event_id="evt-status-1", **payload)

    created = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": "evt-status-1", "x-webhook-signature": signature},
        json=payload,
    ).json()

    close_res = client.post(f"/v1/whatsapp/conversations/{created['thread_id']}/close", headers=headers)
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"

    closed_list = client.get("/v1/whatsapp/conversations?status=closed", headers=headers)
    assert closed_list.status_code == 200
    assert closed_list.json()["total"] == 1

    reopen_res = client.post(f"/v1/whatsapp/conversations/{created['thread_id']}/reopen", headers=headers)
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "open"
