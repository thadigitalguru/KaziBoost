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


def test_same_slug_language_variants_render_with_switcher():
    headers = _auth_headers("langswitch@example.com", "Bilingual Biz")

    site = client.post(
        "/v1/sites",
        headers=headers,
        json={"name": "Bilingual Biz", "template_key": "clinic-basic", "primary_language": "en"},
    ).json()

    en_page = client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={"slug": "services", "title": "Our Services", "language": "en", "body_blocks": ["hero"]},
    )
    sw_page = client.post(
        f"/v1/sites/{site['id']}/pages",
        headers=headers,
        json={"slug": "services", "title": "Huduma Zetu", "language": "sw", "body_blocks": ["hero"]},
    )

    assert en_page.status_code == 201
    assert sw_page.status_code == 201

    client.post(f"/v1/sites/{site['id']}/publish", headers=headers)

    rendered = client.get(f"/v1/sites/{site['id']}/pages/services/render?language=sw", headers=headers)
    assert rendered.status_code == 200
    assert '<html lang="sw">' in rendered.text
    assert "Huduma Zetu" in rendered.text
    assert 'data-language-switcher="true"' in rendered.text
    assert '?language=en' in rendered.text
    assert '?language=sw' in rendered.text
