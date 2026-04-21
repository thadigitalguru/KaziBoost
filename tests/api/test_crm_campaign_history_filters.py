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


def test_campaign_history_can_filter_by_channel():
    headers = _auth_headers("campfilter@example.com", "Campaign Filter Shop")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Lead Form", "kind": "lead", "fields": ["name", "email"]},
    ).json()
    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "Lead One",
            "phone": "+254700121001",
            "email": "lead1@example.com",
            "message": "Interested",
            "source": "web_form",
            "tags": ["vip"],
        },
    )

    client.post(
        "/v1/crm/campaigns/send",
        headers=headers,
        json={"channel": "email", "subject": "Email Offer", "message": "Promo", "tag": "vip"},
    )
    client.post(
        "/v1/crm/campaigns/send",
        headers=headers,
        json={"channel": "sms", "subject": "SMS Offer", "message": "Promo", "tag": "vip"},
    )

    response = client.get("/v1/crm/campaigns/history?channel=email", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["channel"] == "email"
