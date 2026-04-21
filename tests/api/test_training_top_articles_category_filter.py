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


def test_top_articles_can_filter_by_category():
    headers = _auth_headers("topcat@example.com", "Top Category Shop")

    seo = client.post(
        "/v1/training/articles",
        headers=headers,
        json={"title": "SEO Article", "content": "SEO content for training article.", "category": "seo"},
    ).json()
    payments = client.post(
        "/v1/training/articles",
        headers=headers,
        json={"title": "Payments Article", "content": "Payments content for training article.", "category": "payments"},
    ).json()

    client.get(f"/v1/training/articles/{seo['id']}", headers=headers)
    client.get(f"/v1/training/articles/{payments['id']}", headers=headers)

    response = client.get("/v1/training/articles/top?category=seo", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["category"] == "seo"
