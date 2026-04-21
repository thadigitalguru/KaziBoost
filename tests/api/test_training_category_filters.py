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


def test_article_listing_can_filter_by_category():
    headers = _auth_headers("traincat@example.com", "Training Category Shop")

    client.post(
        "/v1/training/articles",
        headers=headers,
        json={"title": "SEO Basics", "content": "SEO basics content for training.", "category": "seo"},
    )
    client.post(
        "/v1/training/articles",
        headers=headers,
        json={"title": "Payments Guide", "content": "Payments guide content for training.", "category": "payments"},
    )

    filtered = client.get("/v1/training/articles?category=seo", headers=headers)
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["category"] == "seo"
