from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


PASSWORD = 'StrongPass123!'


def _signup_and_login(email: str = 'settings-owner@example.com', business_name: str = 'Settings Shop') -> dict[str, str]:
    client.post(
        '/v1/auth/signup',
        json={
            'business_name': business_name,
            'owner_name': 'Owner',
            'email': email,
            'password': PASSWORD,
        },
    )
    login = client.post('/v1/auth/login', json={'email': email, 'password': PASSWORD}).json()
    return {'Authorization': f"Bearer {login['access_token']}"}


def test_settings_profile_reads_and_updates_tenant_controls():
    headers = _signup_and_login()

    profile = client.get('/v1/settings/profile', headers=headers)
    assert profile.status_code == 200
    assert profile.json()['tenant']['name'] == 'Settings Shop'
    assert profile.json()['user']['owner_name'] == 'Owner'

    updated = client.put(
        '/v1/settings/profile',
        headers=headers,
        json={'business_name': 'Updated Shop', 'owner_name': 'Updated Owner'},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body['tenant']['name'] == 'Updated Shop'
    assert body['user']['owner_name'] == 'Updated Owner'

    audit = client.get('/v1/audit/events?entity_type=tenant', headers=headers)
    assert audit.status_code == 200
    assert any(event['event_type'] == 'tenant.profile.updated' for event in audit.json()['items'])


def test_settings_profile_update_requires_owner_role():
    owner_headers = _signup_and_login('settings-owner-2@example.com', 'Settings Shop 2')
    teammate = client.post(
        '/v1/auth/teammates',
        headers=owner_headers,
        json={
            'owner_name': 'Marketer',
            'email': 'settings-marketer@example.com',
            'password': PASSWORD,
            'role': 'marketer',
        },
    ).json()
    teammate_login = client.post('/v1/auth/login', json={'email': 'settings-marketer@example.com', 'password': PASSWORD}).json()
    teammate_headers = {'Authorization': f"Bearer {teammate_login['access_token']}"}

    response = client.put(
        '/v1/settings/profile',
        headers=teammate_headers,
        json={'business_name': 'Nope', 'owner_name': 'Nope'},
    )

    assert response.status_code == 403
