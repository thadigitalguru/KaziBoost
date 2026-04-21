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


def test_featured_articles_filter_returns_only_featured_items():
    headers = _auth_headers("kbfeatured@example.com", "KB Featured Shop")

    a1 = client.post(
        "/v1/training/articles",
        headers=headers,
        json={"title": "Article 1", "content": "Content one for training article.", "category": "seo"},
    ).json()
    client.post(
        "/v1/training/articles",
        headers=headers,
        json={"title": "Article 2", "content": "Content two for training article.", "category": "seo"},
    )

    client.patch(
        f"/v1/training/articles/{a1['id']}",
        headers=headers,
        json={"featured": True},
    )

    featured = client.get("/v1/training/articles?featured=true", headers=headers)
    assert featured.status_code == 200
    assert featured.json()["total"] == 1
    assert featured.json()["items"][0]["id"] == a1["id"]
