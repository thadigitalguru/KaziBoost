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


def test_training_article_update_and_category_listing():
    headers = _auth_headers("kbmgmt@example.com", "KB Mgmt Shop")

    created = client.post(
        "/v1/training/articles",
        headers=headers,
        json={
            "title": "SEO basics",
            "content": "Start with keyword research and optimize pages.",
            "category": "seo-basics",
        },
    ).json()

    updated = client.patch(
        f"/v1/training/articles/{created['id']}",
        headers=headers,
        json={"title": "SEO basics updated", "category": "advanced-seo"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "SEO basics updated"

    categories = client.get("/v1/training/categories", headers=headers)
    assert categories.status_code == 200
    assert "advanced-seo" in categories.json()["items"]
