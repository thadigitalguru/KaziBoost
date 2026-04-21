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


def test_report_schedule_listing_can_filter_by_status():
    headers = _auth_headers("schedfilter@example.com", "Schedule Filter Shop")

    scheduled = client.post(
        "/v1/analytics/reports/schedule",
        headers=headers,
        json={"email": "reports@example.com", "frequency": "weekly"},
    ).json()

    client.delete(f"/v1/analytics/reports/schedules/{scheduled['id']}", headers=headers)

    active = client.get("/v1/analytics/reports/schedules?status=scheduled", headers=headers)
    assert active.status_code == 200
    assert active.json()["total"] == 0

    cancelled = client.get("/v1/analytics/reports/schedules?status=cancelled", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["total"] == 1
    assert cancelled.json()["items"][0]["status"] == "cancelled"
