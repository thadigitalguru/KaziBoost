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


def test_create_site_and_add_page_contracts():
    headers = _auth_headers("sitebuilder1@example.com", "Amina Salon")

    create_site = client.post(
        "/v1/sites",
        headers=headers,
        json={"name": "Amina Salon Site", "template_key": "salon-modern", "primary_language": "en"},
    )

    assert create_site.status_code == 201
    site = create_site.json()
    assert site["name"] == "Amina Salon Site"
    assert site["template_key"] == "salon-modern"
    assert site["status"] == "draft"

    create_page = client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={
            "slug": "home",
            "title": "Welcome to Amina Salon",
            "language": "en",
            "body_blocks": ["hero", "services", "contact"],
        },
    )

    assert create_page.status_code == 201
    page = create_page.json()
    assert page["slug"] == "home"
    assert page["language"] == "en"


def test_publish_generates_sitemap_robots_and_localbusiness_schema():
    headers = _auth_headers("sitebuilder2@example.com", "Kamau Hardware")

    site = client.post(
        "/v1/sites",
        headers=headers,
        json={"name": "Kamau Hardware", "template_key": "hardware-shop", "primary_language": "sw"},
    ).json()

    client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={
            "slug": "home",
            "title": "Karibu Kamau Hardware",
            "language": "sw",
            "body_blocks": ["hero", "products"],
        },
    )
    client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={
            "slug": "about",
            "title": "About Kamau Hardware",
            "language": "en",
            "body_blocks": ["story", "location"],
        },
    )

    publish = client.post(f"/v1/sites/{site['id']}/publish", headers=headers)

    assert publish.status_code == 200
    body = publish.json()
    assert body["status"] == "published"
    assert body["published_url"].startswith("https://")

    sitemap = client.get(f"/v1/sites/{site['id']}/seo/sitemap.xml", headers=headers)
    robots = client.get(f"/v1/sites/{site['id']}/seo/robots.txt", headers=headers)
    schema = client.get(f"/v1/sites/{site['id']}/seo/localbusiness-schema", headers=headers)

    assert sitemap.status_code == 200
    assert "<urlset" in sitemap.text
    assert "/about" in sitemap.text
    assert robots.status_code == 200
    assert "User-agent" in robots.text
    assert "Sitemap:" in robots.text
    assert schema.status_code == 200
    assert schema.json()["@type"] == "LocalBusiness"
    assert schema.json()["name"] == "Kamau Hardware"


def test_mobile_render_has_viewport_meta_tag():
    headers = _auth_headers("sitebuilder3@example.com", "Westlands Vet")

    site = client.post(
        "/v1/sites",
        headers=headers,
        json={"name": "Westlands Vet", "template_key": "clinic-basic", "primary_language": "en"},
    ).json()

    client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={
            "slug": "home",
            "title": "Westlands Vet Home",
            "language": "en",
            "body_blocks": ["hero", "faq"],
        },
    )

    rendered = client.get(f"/v1/sites/{site['id']}/pages/home/render?device=mobile", headers=headers)

    assert rendered.status_code == 200
    assert '<meta name="viewport" content="width=device-width, initial-scale=1"' in rendered.text
    assert "Westlands Vet Home" in rendered.text
