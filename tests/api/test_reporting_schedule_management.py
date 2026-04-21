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


def test_report_schedules_can_be_listed_and_cancelled():
    headers = _auth_headers("reportmgmt@example.com", "Reports Shop")

    scheduled = client.post(
        "/v1/analytics/reports/schedule",
        headers=headers,
        json={"email": "owner@reportshop.co.ke", "frequency": "weekly"},
    ).json()

    listing = client.get("/v1/analytics/reports/schedules", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    cancelled = client.delete(f"/v1/analytics/reports/schedules/{scheduled['id']}", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    listing_after = client.get("/v1/analytics/reports/schedules", headers=headers).json()
    target = [item for item in listing_after["items"] if item["id"] == scheduled["id"]][0]
    assert target["status"] == "cancelled"
