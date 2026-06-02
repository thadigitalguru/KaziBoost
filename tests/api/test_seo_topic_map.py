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


def test_topic_map_generation_returns_pillar_clusters_and_internal_links():
    headers = _auth_headers("topicmap@example.com", "SEO Biz")

    response = client.post(
        "/v1/seo/topic-map/generate",
        headers=headers,
        json={"seed_keyword": "salon marketing", "location": "Westlands", "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pillar_topic"].startswith("Salon Marketing")
    assert len(body["cluster_topics"]) >= 4
    assert len(body["internal_links"]) >= 3
    assert all("anchor_text" in item for item in body["internal_links"])
