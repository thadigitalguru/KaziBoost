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


def test_workspace_delete_clears_saved_keywords():
    headers = _auth_headers("seodel@example.com", "SEO Delete Shop")

    client.post(
        "/v1/seo/keywords/save",
        headers=headers,
        json={"workspace": "local-seo", "keywords": ["best salon westlands", "salon near me"]},
    )

    deleted = client.delete("/v1/seo/keywords/workspaces/local-seo", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    fetched = client.get("/v1/seo/keywords/workspaces/local-seo", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["count"] == 0
