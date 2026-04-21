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


def test_calendar_list_filters_by_status():
    headers = _auth_headers("calfilter@example.com", "Calendar Filter Shop")

    item = client.post(
        "/v1/seo/calendar/items",
        headers=headers,
        json={"title": "Post A", "keyword": "keyword a", "scheduled_for": "2026-07-01", "language": "en"},
    ).json()

    client.post(
        "/v1/seo/calendar/items",
        headers=headers,
        json={"title": "Post B", "keyword": "keyword b", "scheduled_for": "2026-07-02", "language": "en"},
    )

    client.patch(
        f"/v1/seo/calendar/items/{item['id']}",
        headers=headers,
        json={"status": "cancelled"},
    )

    filtered = client.get("/v1/seo/calendar/items?status=cancelled", headers=headers)
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert all(x["status"] == "cancelled" for x in filtered.json()["items"])
