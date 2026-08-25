from fastapi.testclient import TestClient

from kaziboost_api.main import app


client = TestClient(app)


PASSWORD = 'StrongPass123!'


def _auth_headers(email: str = 'feedback-owner@example.com', business_name: str = 'Feedback Shop') -> dict[str, str]:
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


def test_support_feedback_is_recorded_as_an_audit_event():
    headers = _auth_headers()

    response = client.post(
        '/v1/support/feedback',
        headers=headers,
        json={'page': '/dashboard', 'message': 'The onboarding progress should be more prominent.'},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'received'
    assert body['feedback_id'].startswith('feedback-')

    events = client.get('/v1/audit/events?entity_type=feedback', headers=headers)
    assert events.status_code == 200
    assert any(item['event_type'] == 'feedback.submitted' for item in events.json()['items'])


def test_support_feedback_requires_authentication():
    response = client.post('/v1/support/feedback', json={'page': '/dashboard', 'message': 'Hello there.'})
    assert response.status_code == 401
