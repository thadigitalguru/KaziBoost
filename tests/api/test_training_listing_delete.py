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


def test_training_articles_list_and_delete():
    headers = _auth_headers("kblistdel@example.com", "KB List Delete Shop")

    created = client.post(
        "/v1/training/articles",
        headers=headers,
        json={
            "title": "Local marketing basics",
            "content": "Build a website and collect first-party leads.",
            "category": "marketing-basics",
        },
    ).json()

    listing = client.get("/v1/training/articles", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    deleted = client.delete(f"/v1/training/articles/{created['id']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    listing_after = client.get("/v1/training/articles", headers=headers).json()
    ids = {item["id"] for item in listing_after["items"]}
    assert created["id"] not in ids
