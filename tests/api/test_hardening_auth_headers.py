from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


def test_auth_endpoints_set_no_store_cache_headers():
    signup_payload = {
        "business_name": "Header Shop",
        "owner_name": "Owner",
        "email": "headershop@example.com",
        "password": "StrongPass123!",
    }
    client.post("/v1/auth/signup", json=signup_payload)
    login = client.post(
        "/v1/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    )

    assert login.status_code == 200
    assert login.headers.get("cache-control") == "no-store"
    assert login.headers.get("pragma") == "no-cache"
