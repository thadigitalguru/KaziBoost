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


def test_create_and_list_analytics_connectors():
    headers = _auth_headers("connectors@example.com", "Connector Biz")

    ga4 = client.post(
        "/v1/analytics/connectors",
        headers=headers,
        json={"provider": "ga4", "property_id": "GA4-123", "status": "connected"},
    )
    gsc = client.post(
        "/v1/analytics/connectors",
        headers=headers,
        json={"provider": "search_console", "property_id": "sc-domain:domainbiz.co.ke", "status": "connected"},
    )

    assert ga4.status_code == 201
    assert gsc.status_code == 201

    listed = client.get("/v1/analytics/connectors", headers=headers)
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 2
    assert {item["provider"] for item in body["items"]} == {"ga4", "search_console"}
