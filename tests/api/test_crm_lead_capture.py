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


def test_form_submission_creates_contact_with_source_attribution():
    headers = _auth_headers("crm1@example.com", "Amina Salon")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Homepage Lead Form", "kind": "lead", "fields": ["name", "phone", "email", "message"]},
    )
    assert form.status_code == 201
    form_id = form.json()["id"]

    submit = client.post(
        f"/v1/crm/forms/{form_id}/submit",
        headers=headers,
        json={
            "name": "Jane Doe",
            "phone": "+254700123456",
            "email": "jane.doe@example.com",
            "message": "Need salon booking tomorrow",
            "source": "web_form",
            "tags": ["new-lead", "salon"],
        },
    )

    assert submit.status_code == 201
    lead = submit.json()
    assert lead["source"] == "web_form"
    assert lead["contact"]["email"] == "jane.doe@example.com"
    assert "new-lead" in lead["contact"]["tags"]


def test_contacts_can_be_filtered_by_source_and_tag_and_exported_csv():
    headers = _auth_headers("crm2@example.com", "Kamau Hardware")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Quote Form", "kind": "quote", "fields": ["name", "phone", "message"]},
    ).json()

    submissions = [
        {
            "name": "Lead One",
            "phone": "+254700000001",
            "email": "lead1@example.com",
            "message": "Need a wheelbarrow",
            "source": "web_form",
            "tags": ["new", "hardware"],
        },
        {
            "name": "Lead Two",
            "phone": "+254700000002",
            "email": "lead2@example.com",
            "message": "Looking for nails",
            "source": "whatsapp",
            "tags": ["repeat", "hardware"],
        },
    ]

    for payload in submissions:
        response = client.post(f"/v1/crm/forms/{form['id']}/submit", headers=headers, json=payload)
        assert response.status_code == 201

    filtered = client.get("/v1/crm/contacts?source=web_form&tag=new", headers=headers)
    assert filtered.status_code == 200
    body = filtered.json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == "lead1@example.com"

    export_csv = client.get("/v1/crm/contacts/export.csv?source=web_form", headers=headers)
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]
    assert "lead1@example.com" in export_csv.text
    assert "lead2@example.com" not in export_csv.text


def test_contact_timeline_contains_form_submission_interaction():
    headers = _auth_headers("crm3@example.com", "Westlands Vet")

    form = client.post(
        "/v1/crm/forms",
        headers=headers,
        json={"name": "Booking Form", "kind": "booking", "fields": ["name", "phone", "pet", "date"]},
    ).json()

    lead = client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=headers,
        json={
            "name": "John Kariuki",
            "phone": "+254711111111",
            "email": "john.k@example.com",
            "message": "Need vet appointment",
            "source": "web_form",
            "tags": ["pet-owner"],
        },
    ).json()

    timeline = client.get(f"/v1/crm/contacts/{lead['contact']['id']}/timeline", headers=headers)
    assert timeline.status_code == 200
    events = timeline.json()["events"]
    assert len(events) >= 1
    assert events[0]["type"] == "form_submission"
    assert events[0]["source"] == "web_form"
