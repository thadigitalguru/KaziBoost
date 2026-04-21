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


def test_dashboard_trend_snapshot_returns_time_series_shape():
    headers = _auth_headers("trend@example.com", "Trend Shop")

    trend = client.get("/v1/analytics/dashboard/trend?days=7", headers=headers)
    assert trend.status_code == 200
    body = trend.json()
    assert body["days"] == 7
    assert len(body["series"]) == 7
    assert {"date", "leads", "payments"}.issubset(body["series"][0].keys())
