from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


def test_signup_creates_owner_and_tenant_contract():
    payload = {
        "business_name": "Amina Salon",
        "owner_name": "Amina",
        "email": "amina@example.com",
        "password": "StrongPass123!",
    }

    response = client.post("/v1/auth/signup", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == payload["email"]
    assert body["user"]["role"] == "owner"
    assert body["tenant"]["name"] == payload["business_name"]
    assert "tenant_id" in body["user"]


def test_login_returns_access_token_and_context():
    signup_payload = {
        "business_name": "Kamau Hardware",
        "owner_name": "Kamau",
        "email": "kamau@example.com",
        "password": "StrongPass123!",
    }
    client.post("/v1/auth/signup", json=signup_payload)

    response = client.post(
        "/v1/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == signup_payload["email"]


def test_me_endpoint_is_tenant_isolated():
    payload_1 = {
        "business_name": "Westlands Vet",
        "owner_name": "Dr. Wanjiku",
        "email": "wanjiku@example.com",
        "password": "StrongPass123!",
    }
    payload_2 = {
        "business_name": "CBD Clinic",
        "owner_name": "Otieno",
        "email": "otieno@example.com",
        "password": "StrongPass123!",
    }

    client.post("/v1/auth/signup", json=payload_1)
    client.post("/v1/auth/signup", json=payload_2)

    login_1 = client.post(
        "/v1/auth/login",
        json={"email": payload_1["email"], "password": payload_1["password"]},
    ).json()
    login_2 = client.post(
        "/v1/auth/login",
        json={"email": payload_2["email"], "password": payload_2["password"]},
    ).json()

    me_1 = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {login_1['access_token']}"})
    me_2 = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {login_2['access_token']}"})

    assert me_1.status_code == 200
    assert me_2.status_code == 200
    assert me_1.json()["tenant"]["name"] == payload_1["business_name"]
    assert me_2.json()["tenant"]["name"] == payload_2["business_name"]
    assert me_1.json()["tenant"]["id"] != me_2.json()["tenant"]["id"]
