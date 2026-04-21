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


def test_report_schedule_listing_can_filter_by_frequency():
    headers = _auth_headers("schedfreq@example.com", "Schedule Frequency Shop")

    client.post(
        "/v1/analytics/reports/schedule",
        headers=headers,
        json={"email": "weekly@example.com", "frequency": "weekly"},
    )
    client.post(
        "/v1/analytics/reports/schedule",
        headers=headers,
        json={"email": "monthly@example.com", "frequency": "monthly"},
    )

    response = client.get("/v1/analytics/reports/schedules?frequency=monthly", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["frequency"] == "monthly"
