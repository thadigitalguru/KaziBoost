from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


def test_logout_revokes_bearer_token():
    signup_payload = {
        "business_name": "Logout Shop",
        "owner_name": "Owner",
        "email": "logout@example.com",
        "password": "StrongPass123!",
    }
    client.post("/v1/auth/signup", json=signup_payload)
    login = client.post(
        "/v1/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    logout = client.post("/v1/auth/logout", headers=headers)
    assert logout.status_code == 200
    assert logout.json()["status"] == "logged_out"

    me = client.get("/v1/auth/me", headers=headers)
    assert me.status_code == 401
    assert me.json()["detail"] == "Invalid token"
