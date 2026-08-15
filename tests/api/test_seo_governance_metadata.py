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


def test_generated_content_exposes_governance_metadata_and_audit_event():
    headers = _auth_headers("govseo1@example.com", "Governance SEO Shop")

    response = client.post(
        "/v1/seo/content/generate",
        headers=headers,
        json={
            "keyword": "best salon westlands",
            "content_type": "blog",
            "tone": "formal",
            "language": "en",
            "length": "short",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["prompt_version"] == "seo-deterministic-v1"
    assert body["generation_mode"] == "deterministic_template"
    assert body["safety_outcome"] == "safe"
    assert body["policy_violations"] == []

    history = client.get("/v1/seo/content/history", headers=headers).json()
    assert history["items"][0]["prompt_version"] == "seo-deterministic-v1"
    assert history["items"][0]["safety_outcome"] == "safe"

    events = client.get("/v1/audit/events?entity_type=seo_content", headers=headers)
    assert events.status_code == 200
    event_types = {item["event_type"] for item in events.json()["items"]}
    assert "seo.content.generated" in event_types


def test_blocked_content_records_safety_audit_event():
    headers = _auth_headers("govseo2@example.com", "Governance SEO Shop 2")

    response = client.post(
        "/v1/seo/content/generate",
        headers=headers,
        json={
            "keyword": "how to scam customers in nairobi",
            "content_type": "blog",
            "tone": "formal",
            "language": "en",
            "length": "short",
        },
    )

    assert response.status_code == 400

    events = client.get("/v1/audit/events?entity_type=seo_content", headers=headers).json()
    assert any(item["event_type"] == "seo.content.blocked" for item in events["items"])
