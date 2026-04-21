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


def test_top_articles_sorted_by_views_desc():
    headers = _auth_headers("kbtop@example.com", "KB Top Shop")

    a1 = client.post(
        "/v1/training/articles",
        headers=headers,
        json={"title": "Article A", "content": "Alpha content for training article.", "category": "seo"},
    ).json()
    a2 = client.post(
        "/v1/training/articles",
        headers=headers,
        json={"title": "Article B", "content": "Beta content for training article.", "category": "seo"},
    ).json()

    client.get(f"/v1/training/articles/{a1['id']}", headers=headers)
    client.get(f"/v1/training/articles/{a1['id']}", headers=headers)
    client.get(f"/v1/training/articles/{a2['id']}", headers=headers)

    top = client.get("/v1/training/articles/top", headers=headers)
    assert top.status_code == 200
    assert top.json()["total"] >= 2
    assert top.json()["items"][0]["id"] == a1["id"]
