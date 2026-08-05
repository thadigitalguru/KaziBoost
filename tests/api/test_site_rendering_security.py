from html import escape
from urllib.parse import quote

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


def test_rendered_site_html_escapes_tenant_controlled_fields():
    headers = _auth_headers("renderxss@example.com", 'Amina "Growth"')
    site_name = 'Amina <script>alert("site")</script> & "Co"'
    template_key = 'tpl"><img'
    slug = 'offer"q'
    primary_language = 'en"x=<'
    alternate_language = 'sw"y=<'
    page_title = 'Deal <script>alert("page")</script> "today"'

    site_response = client.post(
        "/v1/sites",
        headers=headers,
        json={"name": site_name, "template_key": template_key, "primary_language": primary_language},
    )
    assert site_response.status_code == 201
    site = site_response.json()

    primary_page = client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={
            "slug": slug,
            "title": page_title,
            "language": primary_language,
            "body_blocks": ["hero"],
        },
    )
    alternate_page = client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={
            "slug": slug,
            "title": "Huduma",
            "language": alternate_language,
            "body_blocks": ["hero"],
        },
    )
    assert primary_page.status_code == 201
    assert alternate_page.status_code == 201

    publish = client.post(f"/v1/sites/{site['id']}/publish", headers=headers)
    assert publish.status_code == 200

    rendered = client.get(
        f"/v1/sites/{site['id']}/pages/{quote(slug, safe='')}/render?language={quote(primary_language, safe='')}",
        headers=headers,
    )

    assert rendered.status_code == 200
    html = rendered.text
    escaped_title = escape(page_title, quote=True)
    escaped_site_name = escape(site_name, quote=True)
    escaped_template_key = escape(template_key, quote=True)
    escaped_language = escape(primary_language, quote=True)

    assert f'<html lang="{escaped_language}">' in html
    assert f"<title>{escaped_title}</title>" in html
    assert f'<meta name="description" content="{escaped_site_name} - {escaped_title}" />' in html
    assert f"<h1>{escaped_title}</h1>" in html
    assert f"Template: {escaped_template_key}" in html
    assert 'data-language-switcher="true"' in html
    assert f'?language={quote(primary_language, safe="")}' in html
    assert f'?language={quote(alternate_language, safe="")}' in html
    assert f"/{quote(slug, safe='')}?language={quote(primary_language, safe='')}" in html

    assert page_title not in html
    assert site_name not in html
    assert template_key not in html
    assert primary_language not in html
