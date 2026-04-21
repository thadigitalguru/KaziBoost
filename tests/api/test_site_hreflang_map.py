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


def test_hreflang_map_includes_multilingual_page_variants():
    headers = _auth_headers("hreflang@example.com", "Hreflang Shop")

    site = client.post(
        "/v1/sites",
        headers=headers,
        json={"name": "Hreflang Shop", "template_key": "salon-modern", "primary_language": "en"},
    ).json()

    client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={"slug": "services-en", "title": "Services", "language": "en", "body_blocks": ["hero"]},
    )
    client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={"slug": "services-sw", "title": "Huduma", "language": "sw", "body_blocks": ["hero"]},
    )

    client.post(f"/v1/sites/{site['id']}/publish", headers=headers)

    mapping = client.get(f"/v1/sites/{site['id']}/seo/hreflang-map", headers=headers)
    assert mapping.status_code == 200
    body = mapping.json()
    assert body["total"] >= 2
    languages = {item["language"] for item in body["items"]}
    assert "en" in languages
    assert "sw" in languages
