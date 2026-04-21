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


def test_calendar_item_can_be_deleted():
    headers = _auth_headers("seodelitem@example.com", "SEO Delete Item Shop")

    created = client.post(
        "/v1/seo/calendar/items",
        headers=headers,
        json={"title": "Delete me", "keyword": "delete kw", "scheduled_for": "2026-09-01", "language": "en"},
    ).json()

    deleted = client.delete(f"/v1/seo/calendar/items/{created['id']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    listed = client.get("/v1/seo/calendar/items", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 0
