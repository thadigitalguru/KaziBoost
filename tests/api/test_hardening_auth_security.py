from fastapi.testclient import TestClient

from kaziboost_api.main import app
from kaziboost_api.store import store


client = TestClient(app)


def test_signup_rejects_weak_password():
    response = client.post(
        "/v1/auth/signup",
        json={
            "business_name": "Weak Password Shop",
            "owner_name": "Owner",
            "email": "weak@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert "Password" in response.json()["detail"]


def test_login_rate_limited_after_repeated_failures():
    signup_payload = {
        "business_name": "Rate Limit Shop",
        "owner_name": "Owner",
        "email": "ratelimit@example.com",
        "password": "StrongPass123!",
    }
    client.post("/v1/auth/signup", json=signup_payload)

    for _ in range(5):
        failed = client.post(
            "/v1/auth/login",
            json={"email": signup_payload["email"], "password": "WrongPass123!"},
        )
        assert failed.status_code == 401

    blocked = client.post(
        "/v1/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    )
    assert blocked.status_code == 429


def test_expired_token_is_rejected():
    signup_payload = {
        "business_name": "Token Expiry Shop",
        "owner_name": "Owner",
        "email": "tokenexpiry@example.com",
        "password": "StrongPass123!",
    }
    client.post("/v1/auth/signup", json=signup_payload)

    login = client.post(
        "/v1/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    ).json()

    store.force_expire_token_for_test(login["access_token"])

    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})
    assert me.status_code == 401
    assert me.json()["detail"] == "Token expired"
