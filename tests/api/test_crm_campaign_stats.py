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


def test_campaign_stats_channel_breakdown_and_recipients():
    headers = _auth_headers("campstats@example.com", "Campaign Stats Shop")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Lead Form", "kind": "lead", "fields": ["name", "email"]},
    ).json()

    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "VIP",
            "phone": "+254700721001",
            "email": "vip@stats.example",
            "message": "hello",
            "source": "web_form",
            "tags": ["vip"],
        },
    )

    client.post(
        "/v1/crm/campaigns/send",
        headers=headers,
        json={"channel": "email", "subject": "Offer A", "message": "Offer message A", "tag": "vip"},
    )
    client.post(
        "/v1/crm/campaigns/send",
        headers=headers,
        json={"channel": "sms", "subject": "Offer B", "message": "Offer message B", "tag": "vip"},
    )

    stats = client.get("/v1/crm/campaigns/stats", headers=headers)
    assert stats.status_code == 200
    body = stats.json()
    assert body["total_campaigns"] >= 2
    assert body["total_recipients"] >= 2
    assert body["by_channel"]["email"] >= 1
    assert body["by_channel"]["sms"] >= 1
