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


def test_content_generation_rejects_unsafe_keywords():
    headers = _auth_headers("seosafe1@example.com", "SEO Safety Shop")

    response = client.post(
        "/v1/seo/content/generate",
        headers=headers,
        json={
            "keyword": "how to scam customers in nairobi",
            "content_type": "blog",
            "tone": "conversational",
            "language": "en",
            "length": "medium",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "bad_request"


def test_content_history_retains_only_safe_generated_content():
    headers = _auth_headers("seosafe2@example.com", "SEO Safety Shop 2")

    good = client.post(
        "/v1/seo/content/generate",
        headers=headers,
        json={
            "keyword": "best salon westlands",
            "content_type": "blog",
            "tone": "formal",
            "language": "en",
            "length": "short",
        },
    )
    assert good.status_code == 200

    history = client.get("/v1/seo/content/history", headers=headers).json()
    assert history["total"] >= 1
    assert all("scam" not in item["keyword"] for item in history["items"])
