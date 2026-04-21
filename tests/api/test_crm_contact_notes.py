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


def test_contact_notes_create_and_list():
    headers = _auth_headers("notes1@example.com", "Notes Shop")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Lead Form", "kind": "lead", "fields": ["name", "email"]},
    ).json()

    lead = client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "Contact A",
            "phone": "+254700801555",
            "email": "contacta@example.com",
            "message": "Interested",
            "source": "web_form",
            "tags": ["warm"],
        },
    ).json()

    note = client.post(
        f"/v1/crm/contacts/{lead['contact']['id']}/notes",
        headers=headers,
        json={"text": "Called customer, requested follow-up tomorrow."},
    )
    assert note.status_code == 201

    listing = client.get(f"/v1/crm/contacts/{lead['contact']['id']}/notes", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1
    assert "follow-up" in listing.json()["items"][0]["text"]
