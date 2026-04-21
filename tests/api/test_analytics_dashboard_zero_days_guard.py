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


def test_dashboard_trend_rejects_non_positive_day_windows():
    headers = _auth_headers("trendguard@example.com", "Trend Guard Shop")

    response = client.get("/v1/analytics/dashboard/trend?days=0", headers=headers)
    assert response.status_code == 400
    assert "days" in str(response.json()["detail"]).lower()
