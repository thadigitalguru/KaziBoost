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


def _create_contact(headers: dict[str, str], unique: str) -> str:
    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Lead Form", "kind": "lead", "fields": ["name", "email"]},
    ).json()
    lead = client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": f"Lead {unique}",
            "phone": "+254700300300",
            "email": f"lead-{unique}@example.com",
            "message": "Need support",
            "source": "web_form",
            "tags": ["lead"],
        },
    ).json()
    return lead["contact"]["id"]


def test_contact_consent_update_and_export():
    headers = _auth_headers("crmcomp1@example.com", "Amina Salon")
    contact_id = _create_contact(headers, "c1")

    consent = client.patch(
        f"/v1/crm/contacts/{contact_id}/consent",
        headers=headers,
        json={"email_marketing": True, "sms_marketing": False},
    )
    assert consent.status_code == 200
    assert consent.json()["consent"]["email_marketing"] is True

    exported = client.get(f"/v1/crm/contacts/{contact_id}/export", headers=headers)
    assert exported.status_code == 200
    assert exported.json()["contact"]["id"] == contact_id
    assert exported.json()["contact"]["consent"]["email_marketing"] is True


def test_contact_anonymization_masks_pii():
    headers = _auth_headers("crmcomp2@example.com", "Kamau Hardware")
    contact_id = _create_contact(headers, "c2")

    deleted = client.delete(f"/v1/crm/contacts/{contact_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "anonymized"

    exported = client.get(f"/v1/crm/contacts/{contact_id}/export", headers=headers)
    assert exported.status_code == 200
    assert exported.json()["contact"]["email"].endswith("@redacted.local")
    assert exported.json()["contact"]["name"] == "ANONYMIZED"
