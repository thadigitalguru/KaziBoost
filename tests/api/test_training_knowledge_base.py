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


def test_knowledge_base_article_create_and_search():
    headers = _auth_headers("kb1@example.com", "KB Shop")

    created = client.post(
        "/v1/training/articles",
        headers=headers,
        json={
            "title": "How to improve local SEO in Nairobi",
            "content": "Use localized keywords, optimize GBP listings, and publish FAQs.",
            "category": "seo-basics",
        },
    )
    assert created.status_code == 201

    search = client.get("/v1/training/articles/search?q=localized", headers=headers)
    assert search.status_code == 200
    assert search.json()["total"] >= 1
    assert search.json()["items"][0]["title"] == "How to improve local SEO in Nairobi"
