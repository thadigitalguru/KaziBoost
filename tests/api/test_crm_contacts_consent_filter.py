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


def test_contacts_can_filter_by_email_marketing_consent():
    headers = _auth_headers("consentfilter@example.com", "Consent Filter Shop")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Lead Form", "kind": "lead", "fields": ["name", "email"]},
    ).json()

    contact_1 = client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "Lead Yes",
            "phone": "+254700121111",
            "email": "leadyes@example.com",
            "message": "Interested",
            "source": "web_form",
            "tags": ["vip"],
        },
    ).json()["contact"]
    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "Lead No",
            "phone": "+254700121112",
            "email": "leadno@example.com",
            "message": "Interested",
            "source": "web_form",
            "tags": ["vip"],
        },
    )

    client.patch(
        f"/v1/crm/contacts/{contact_1['id']}/consent",
        headers=headers,
        json={"email_marketing": True, "sms_marketing": False},
    )

    response = client.get("/v1/crm/contacts?email_marketing=true", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == contact_1["id"]
