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


def test_site_custom_domain_updates_published_url_and_seo_assets():
    headers = _auth_headers("domain1@example.com", "Domain Biz")

    site = client.post(
        "/v1/sites",
        headers=headers,
        json={"name": "Domain Biz Site", "template_key": "salon-modern", "primary_language": "en"},
    ).json()

    client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={"slug": "home", "title": "Home", "language": "en", "body_blocks": ["hero"]},
    )

    domain = client.post(
        f"/v1/sites/{site['id']}/domain",
        headers=headers,
        json={"domain": "www.domainbiz.co.ke"},
    )
    assert domain.status_code == 200
    assert domain.json()["domain"] == "www.domainbiz.co.ke"

    publish = client.post(f"/v1/sites/{site['id']}/publish", headers=headers)
    assert publish.status_code == 200
    assert publish.json()["published_url"] == "https://www.domainbiz.co.ke"

    sitemap = client.get(f"/v1/sites/{site['id']}/seo/sitemap.xml", headers=headers)
    assert "https://www.domainbiz.co.ke/" in sitemap.text
