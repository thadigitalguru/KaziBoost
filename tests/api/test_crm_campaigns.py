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


def test_campaign_send_to_tagged_contacts_and_history():
    headers = _auth_headers("campaign1@example.com", "Campaign Shop")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Lead Form", "kind": "lead", "fields": ["name", "email"]},
    ).json()

    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "VIP Lead",
            "phone": "+254700111221",
            "email": "vip-lead@example.com",
            "message": "Interested",
            "source": "web_form",
            "tags": ["vip"],
        },
    )

    send = client.post(
        "/v1/crm/campaigns/send",
        headers=headers,
        json={
            "channel": "email",
            "subject": "VIP Offer",
            "message": "Hello VIP customer",
            "tag": "vip",
        },
    )

    assert send.status_code == 201
    assert send.json()["recipients"] == 1

    history = client.get("/v1/crm/campaigns/history", headers=headers)
    assert history.status_code == 200
    assert history.json()["total"] >= 1
    assert history.json()["items"][0]["subject"] == "VIP Offer"
