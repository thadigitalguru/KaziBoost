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


def test_high_volume_list_routes_validate_pagination_bounds():
    headers = _auth_headers("pagination-contracts@example.com", "Pagination Contracts Shop")
    routes = [
        "/v1/whatsapp/conversations",
        "/v1/whatsapp/reminders/history",
        "/v1/whatsapp/queue/overdue",
        "/v1/payments/reconciliation?contact_id=missing",
        "/v1/payments/missing/refunds",
        "/v1/payments/failures",
        "/v1/training/articles",
        "/v1/seo/calendar/items",
        "/v1/seo/calendar/due?on_or_before=2026-08-06",
    ]

    for route in routes:
        response = client.get(f"{route}&limit=0" if "?" in route else f"{route}?limit=0", headers=headers)
        assert response.status_code == 422, route

    assert client.get("/v1/crm/contacts?offset=10001", headers=headers).status_code == 422
