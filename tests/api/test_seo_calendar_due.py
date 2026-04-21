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


def test_due_calendar_items_filtered_by_date_cutoff():
    headers = _auth_headers("caldue@example.com", "Calendar Due Shop")

    client.post(
        "/v1/seo/calendar/items",
        headers=headers,
        json={"title": "Soon", "keyword": "soon kw", "scheduled_for": "2026-07-01", "language": "en"},
    )
    client.post(
        "/v1/seo/calendar/items",
        headers=headers,
        json={"title": "Later", "keyword": "later kw", "scheduled_for": "2026-12-01", "language": "en"},
    )

    due = client.get("/v1/seo/calendar/due?on_or_before=2026-08-01", headers=headers)
    assert due.status_code == 200
    assert due.json()["total"] == 1
    assert due.json()["items"][0]["title"] == "Soon"
