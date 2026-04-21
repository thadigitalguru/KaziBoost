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


def test_calendar_item_status_can_be_cancelled():
    headers = _auth_headers("calstatus@example.com", "Calendar Status Shop")

    item = client.post(
        "/v1/seo/calendar/items",
        headers=headers,
        json={
            "title": "Plumber guide",
            "keyword": "best plumber westlands",
            "scheduled_for": "2026-06-01",
            "language": "en",
        },
    ).json()

    cancelled = client.patch(
        f"/v1/seo/calendar/items/{item['id']}",
        headers=headers,
        json={"status": "cancelled"},
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
