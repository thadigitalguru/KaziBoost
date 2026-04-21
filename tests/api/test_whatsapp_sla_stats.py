from fastapi.testclient import TestClient

from kaziboost_api.main import app
from kaziboost_api.whatsapp_security import build_whatsapp_signature


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


def test_whatsapp_sla_stats_reports_open_handoff_closed_counts():
    headers = _auth_headers("wasla@example.com", "WA SLA Shop")

    payload = {"from_phone": "+254700751001", "message_text": "Need help", "language": "en"}
    sig = build_whatsapp_signature(event_id="evt-sla-1", **payload)
    convo = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": "evt-sla-1", "x-webhook-signature": sig},
        json=payload,
    ).json()

    client.post(
        f"/v1/whatsapp/conversations/{convo['thread_id']}/handoff",
        headers=headers,
        json={"assigned_to": "support-1"},
    )

    stats = client.get("/v1/whatsapp/stats/sla", headers=headers)
    assert stats.status_code == 200
    body = stats.json()
    assert body["totals"]["all"] >= 1
    assert body["totals"]["handoff"] >= 1
