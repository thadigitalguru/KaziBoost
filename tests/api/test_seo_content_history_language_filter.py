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


def test_content_history_can_filter_by_language():
    headers = _auth_headers("seolanghist@example.com", "SEO Lang History Shop")

    client.post(
        "/v1/seo/content/generate",
        headers=headers,
        json={"keyword": "salon nairobi", "content_type": "blog", "tone": "helpful", "language": "en", "length": "short"},
    )
    client.post(
        "/v1/seo/content/generate",
        headers=headers,
        json={"keyword": "saluni nairobi", "content_type": "blog", "tone": "helpful", "language": "sw", "length": "short"},
    )

    response = client.get("/v1/seo/content/history?language=sw", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["language"] == "sw"
