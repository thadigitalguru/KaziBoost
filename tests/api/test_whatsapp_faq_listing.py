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


def test_faq_listing_returns_created_items():
    headers = _auth_headers("wafaq@example.com", "WA FAQ Shop")

    client.post(
        "/v1/whatsapp/faq",
        headers=headers,
        json={"question": "pricing", "answer": "Our pricing starts from KES 1,000."},
    )
    client.post(
        "/v1/whatsapp/faq",
        headers=headers,
        json={"question": "hours", "answer": "We are open 8am to 6pm."},
    )

    response = client.get("/v1/whatsapp/faq", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["items"][0]["question"] == "pricing"
    assert body["items"][1]["question"] == "hours"
