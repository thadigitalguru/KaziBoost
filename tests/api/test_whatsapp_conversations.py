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


def test_whatsapp_incoming_creates_conversation_thread():
    headers = _auth_headers("wa1@example.com", "Amina Salon")

    incoming = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers=headers,
        json={
            "from_phone": "+254700333111",
            "message_text": "Hi, I want to book a salon slot",
            "language": "en",
        },
    )

    assert incoming.status_code == 201
    body = incoming.json()
    assert body["status"] == "open"
    assert body["thread_id"]
    assert body["last_message"] == "Hi, I want to book a salon slot"


def test_whatsapp_conversations_are_listed_per_tenant():
    headers_1 = _auth_headers("wa2@example.com", "Kamau Hardware")
    headers_2 = _auth_headers("wa3@example.com", "Westlands Vet")

    client.post(
        "/v1/whatsapp/webhook/incoming",
        headers=headers_1,
        json={
            "from_phone": "+254700444111",
            "message_text": "Do you sell wheelbarrows?",
            "language": "en",
        },
    )

    client.post(
        "/v1/whatsapp/webhook/incoming",
        headers=headers_2,
        json={
            "from_phone": "+254700555111",
            "message_text": "Need vet appointment tomorrow",
            "language": "en",
        },
    )

    list_1 = client.get("/v1/whatsapp/conversations", headers=headers_1)
    list_2 = client.get("/v1/whatsapp/conversations", headers=headers_2)

    assert list_1.status_code == 200
    assert list_2.status_code == 200
    assert list_1.json()["total"] == 1
    assert list_2.json()["total"] == 1
    assert list_1.json()["items"][0]["from_phone"] == "+254700444111"
    assert list_2.json()["items"][0]["from_phone"] == "+254700555111"
