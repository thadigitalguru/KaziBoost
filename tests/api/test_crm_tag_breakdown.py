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


def test_tag_breakdown_counts_contacts_per_tag():
    headers = _auth_headers("tagbreak@example.com", "Tag Breakdown Shop")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Lead Form", "kind": "lead", "fields": ["name", "email"]},
    ).json()

    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "Lead A",
            "phone": "+254700111001",
            "email": "lead-a@example.com",
            "message": "Interested",
            "source": "web_form",
            "tags": ["vip", "new"],
        },
    )
    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "Lead B",
            "phone": "+254700111002",
            "email": "lead-b@example.com",
            "message": "Interested too",
            "source": "web_form",
            "tags": ["vip"],
        },
    )

    summary = client.get("/v1/crm/analytics/tags", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["totals"]["vip"] == 2
    assert body["totals"]["new"] == 1
