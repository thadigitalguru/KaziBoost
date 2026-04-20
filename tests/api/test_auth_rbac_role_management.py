from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


def _signup_and_login(email: str, business_name: str) -> dict:
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


def test_owner_can_create_teammate_and_update_role():
    owner_headers = _signup_and_login("rbac1@example.com", "RBAC Shop")

    teammate = client.post(
        "/v1/auth/teammates",
        headers=owner_headers,
        json={"owner_name": "Marketer User", "email": "marketer@example.com", "password": "StrongPass123!", "role": "marketer"},
    )
    assert teammate.status_code == 201
    user_id = teammate.json()["user"]["id"]

    updated = client.patch(
        f"/v1/auth/users/{user_id}/role",
        headers=owner_headers,
        json={"role": "manager"},
    )
    assert updated.status_code == 200
    assert updated.json()["user"]["role"] == "manager"


def test_non_owner_cannot_update_roles():
    owner_headers = _signup_and_login("rbac2@example.com", "RBAC Shop 2")

    teammate = client.post(
        "/v1/auth/teammates",
        headers=owner_headers,
        json={"owner_name": "Viewer User", "email": "viewer@example.com", "password": "StrongPass123!", "role": "viewer"},
    ).json()

    viewer_login = client.post(
        "/v1/auth/login",
        json={"email": "viewer@example.com", "password": "StrongPass123!"},
    ).json()
    viewer_headers = {"Authorization": f"Bearer {viewer_login['access_token']}"}

    denied = client.patch(
        f"/v1/auth/users/{teammate['user']['id']}/role",
        headers=viewer_headers,
        json={"role": "manager"},
    )

    assert denied.status_code == 403
