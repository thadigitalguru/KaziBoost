from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


def _signup_and_login(email: str, business_name: str) -> dict[str, str]:
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


def test_owner_can_enroll_and_verify_mfa_challenge():
    headers = _signup_and_login("mfa-owner@example.com", "MFA Biz")

    enrolled = client.post("/v1/auth/mfa/enroll", headers=headers)
    assert enrolled.status_code == 201
    body = enrolled.json()
    assert body["enabled"] is True
    assert body["secret"]
    assert len(body["backup_codes"]) == 3

    challenge = client.post("/v1/auth/mfa/challenge", headers=headers)
    assert challenge.status_code == 201
    challenge_body = challenge.json()
    assert challenge_body["challenge_id"]
    assert challenge_body["status"] == "pending"

    verified = client.post(
        "/v1/auth/mfa/verify",
        headers=headers,
        json={"challenge_id": challenge_body["challenge_id"], "code": challenge_body["test_code"]},
    )
    assert verified.status_code == 200
    assert verified.json()["status"] == "verified"
