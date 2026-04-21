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


def test_create_segment_and_resolve_matching_contacts():
    headers = _auth_headers("seg1@example.com", "Segment Shop")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Lead Form", "kind": "lead", "fields": ["name", "email"]},
    ).json()

    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "VIP One",
            "phone": "+254700400401",
            "email": "vip1@example.com",
            "message": "Need support",
            "source": "web_form",
            "tags": ["vip", "repeat"],
        },
    )
    client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "Regular One",
            "phone": "+254700400402",
            "email": "regular@example.com",
            "message": "Need quote",
            "source": "whatsapp",
            "tags": ["new"],
        },
    )

    segment = client.post(
        "/v1/crm/segments",
        headers=headers,
        json={"name": "VIP Web", "tag": "vip", "source": "web_form"},
    )

    assert segment.status_code == 201
    segment_id = segment.json()["id"]

    resolved = client.get(f"/v1/crm/segments/{segment_id}/contacts", headers=headers)
    assert resolved.status_code == 200
    assert resolved.json()["total"] == 1
    assert resolved.json()["items"][0]["email"] == "vip1@example.com"
