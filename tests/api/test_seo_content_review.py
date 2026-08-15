from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


def _auth_headers(email: str) -> dict[str, str]:
    payload = {
        "business_name": "Review Shop",
        "owner_name": "Owner",
        "email": email,
        "password": "StrongPass123!",
    }
    client.post("/v1/auth/signup", json=payload)
    login = client.post("/v1/auth/login", json={"email": email, "password": payload["password"]}).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def test_generated_content_requires_review_before_linked_calendar_scheduling():
    headers = _auth_headers("review1@example.com")
    generated = client.post(
        "/v1/seo/content/generate",
        headers=headers,
        json={"keyword": "salon westlands", "content_type": "blog", "tone": "helpful", "language": "en", "length": "short"},
    ).json()

    assert generated["id"]
    assert client.post(
        "/v1/seo/calendar/items",
        headers=headers,
        json={
            "title": "Salon guide",
            "keyword": "salon westlands",
            "scheduled_for": "2026-09-01",
            "language": "en",
            "generated_content_id": generated["id"],
        },
    ).json()["status"] == "draft"

    history = client.get("/v1/seo/calendar/items", headers=headers).json()
    item = history["items"][0]
    blocked = client.patch(
        f"/v1/seo/calendar/items/{item['id']}",
        headers=headers,
        json={"status": "scheduled"},
    )
    assert blocked.status_code == 400

    approved = client.patch(
        f"/v1/seo/content/{generated['id']}/review",
        headers=headers,
        json={"status": "approved", "review_note": "Reviewed for local relevance."},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    scheduled = client.patch(
        f"/v1/seo/calendar/items/{item['id']}",
        headers=headers,
        json={"status": "scheduled"},
    )
    assert scheduled.status_code == 200
    assert scheduled.json()["status"] == "scheduled"


def test_review_transitions_and_manual_calendar_compatibility():
    headers = _auth_headers("review2@example.com")
    generated = client.post(
        "/v1/seo/content/generate",
        headers=headers,
        json={"keyword": "vet clinic nairobi", "content_type": "blog", "tone": "helpful", "language": "en", "length": "short"},
    ).json()

    rejected = client.patch(
        f"/v1/seo/content/{generated['id']}/review",
        headers=headers,
        json={"status": "rejected", "review_note": "Needs a clearer local offer."},
    )
    assert rejected.status_code == 200

    approved_rejected = client.patch(
        f"/v1/seo/content/{generated['id']}/review",
        headers=headers,
        json={"status": "approved"},
    )
    assert approved_rejected.status_code == 400

    reopened = client.patch(
        f"/v1/seo/content/{generated['id']}/review",
        headers=headers,
        json={"status": "needs_review"},
    )
    assert reopened.status_code == 200

    manual = client.post(
        "/v1/seo/calendar/items",
        headers=headers,
        json={"title": "Manual post", "keyword": "vet clinic", "scheduled_for": "2026-09-02", "language": "en"},
    )
    assert manual.status_code == 201
    assert manual.json()["status"] == "scheduled"
