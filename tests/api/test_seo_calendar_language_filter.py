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


def test_calendar_listing_can_filter_by_language():
    headers = _auth_headers("callang@example.com", "Calendar Language Shop")

    client.post(
        "/v1/seo/calendar/items",
        headers=headers,
        json={"title": "English Post", "keyword": "salon nairobi", "scheduled_for": "2026-10-01", "language": "en"},
    )
    client.post(
        "/v1/seo/calendar/items",
        headers=headers,
        json={"title": "Swahili Post", "keyword": "saluni nairobi", "scheduled_for": "2026-10-02", "language": "sw"},
    )

    response = client.get("/v1/seo/calendar/items?language=sw", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["language"] == "sw"
