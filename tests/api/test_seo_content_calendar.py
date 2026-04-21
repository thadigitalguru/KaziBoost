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


def test_content_calendar_item_create_and_list():
    headers = _auth_headers("calendar1@example.com", "Calendar Shop")

    created = client.post(
        "/v1/seo/calendar/items",
        headers=headers,
        json={
            "title": "Nairobi salon tips",
            "keyword": "best salon westlands",
            "scheduled_for": "2026-05-10",
            "language": "en",
        },
    )

    assert created.status_code == 201
    assert created.json()["status"] == "scheduled"

    listing = client.get("/v1/seo/calendar/items", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1
    assert listing.json()["items"][0]["title"] == "Nairobi salon tips"
