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


def test_lead_sources_summary_counts_contacts_by_source():
    headers = _auth_headers("leadsrc@example.com", "Lead Source Shop")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Lead Form", "kind": "lead", "fields": ["name", "email"]},
    ).json()

    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "Lead Web",
            "phone": "+254700900111",
            "email": "lead-web@example.com",
            "message": "Need quote",
            "source": "web_form",
            "tags": ["new"],
        },
    )
    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "Lead WA",
            "phone": "+254700900112",
            "email": "lead-wa@example.com",
            "message": "Need pricing",
            "source": "whatsapp",
            "tags": ["new"],
        },
    )

    summary = client.get("/v1/crm/analytics/lead-sources", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["totals"]["web_form"] >= 1
    assert summary.json()["totals"]["whatsapp"] >= 1
