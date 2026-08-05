from fastapi.testclient import TestClient

from kaziboost_api.main import app
from kaziboost_api.payments_security import build_mpesa_callback_signature
from kaziboost_api.whatsapp_security import build_whatsapp_signature


client = TestClient(app)


PASSWORD = "StrongPass123!"


def _signup_and_login(email: str, business_name: str) -> dict[str, str]:
    signup_payload = {
        "business_name": business_name,
        "owner_name": "Owner",
        "email": email,
        "password": PASSWORD,
    }
    client.post("/v1/auth/signup", json=signup_payload)
    login = client.post(
        "/v1/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    ).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def _teammate_headers(owner_headers: dict[str, str], role: str, email: str) -> dict[str, str]:
    created = client.post(
        "/v1/auth/teammates",
        headers=owner_headers,
        json={"owner_name": f"{role.title()} User", "email": email, "password": PASSWORD, "role": role},
    )
    assert created.status_code == 201
    login = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD}).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def _create_contact(owner_headers: dict[str, str], suffix: str) -> str:
    form = client.post(
        "/v1/crm/forms",
        headers=owner_headers,
        json={"name": f"Lead form {suffix}", "kind": "lead", "fields": ["name", "phone", "email"]},
    ).json()
    submission = client.post(
        f"/v1/crm/forms/{form['id']}/submit",
        headers=owner_headers,
        json={
            "name": f"Lead {suffix}",
            "phone": "+254700111222",
            "email": f"lead-{suffix}@example.com",
            "message": "Interested in services",
            "source": "web_form",
            "tags": ["new"],
        },
    )
    assert submission.status_code == 201
    return submission.json()["contact"]["id"]


def _create_successful_payment(owner_headers: dict[str, str], suffix: str, contact_id: str | None = None) -> str:
    initiated = client.post(
        "/v1/payments/mpesa/initiate",
        headers=owner_headers,
        json={
            "phone": "+254700123456",
            "amount": 1000,
            "currency": "KES",
            "reference": f"ORDER-{suffix}",
            "contact_id": contact_id,
        },
    )
    assert initiated.status_code == 201
    payment_id = initiated.json()["payment_id"]
    provider_tx_id = f"TX-{suffix}"
    callback = client.post(
        "/v1/payments/mpesa/callback",
        headers={
            **owner_headers,
            "x-callback-signature": build_mpesa_callback_signature(payment_id, provider_tx_id, "success"),
        },
        json={"payment_id": payment_id, "provider_tx_id": provider_tx_id, "status": "success"},
    )
    assert callback.status_code == 200
    return payment_id


def _create_whatsapp_thread(owner_headers: dict[str, str], suffix: str) -> str:
    event_id = f"evt-rbac-{suffix}"
    payload = {"from_phone": "+254700333111", "message_text": "Hi, I need help", "language": "en"}
    incoming = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={
            **owner_headers,
            "x-event-id": event_id,
            "x-webhook-signature": build_whatsapp_signature(
                event_id,
                payload["from_phone"],
                payload["message_text"],
                payload["language"],
            ),
        },
        json=payload,
    )
    assert incoming.status_code == 201
    return incoming.json()["thread_id"]


def test_site_role_matrix_allows_content_roles_and_blocks_admin_roles():
    owner = _signup_and_login("role-sites-owner@example.com", "Role Sites")
    viewer = _teammate_headers(owner, "viewer", "role-sites-viewer@example.com")
    marketer = _teammate_headers(owner, "marketer", "role-sites-marketer@example.com")
    manager = _teammate_headers(owner, "manager", "role-sites-manager@example.com")

    denied_create = client.post(
        "/v1/sites",
        headers=viewer,
        json={"name": "Viewer Site", "template_key": "salon-modern", "primary_language": "en"},
    )
    assert denied_create.status_code == 403
    assert client.get("/v1/sites", headers=viewer).status_code == 200

    marketer_site = client.post(
        "/v1/sites",
        headers=marketer,
        json={"name": "Marketer Site", "template_key": "salon-modern", "primary_language": "en"},
    )
    assert marketer_site.status_code == 201

    denied_domain = client.post(
        f"/v1/sites/{marketer_site.json()['id']}/domain",
        headers=marketer,
        json={"domain": "marketer.example.com"},
    )
    assert denied_domain.status_code == 403

    attached_domain = client.post(
        f"/v1/sites/{marketer_site.json()['id']}/domain",
        headers=manager,
        json={"domain": "manager.example.com"},
    )
    assert attached_domain.status_code == 200


def test_crm_role_matrix_restricts_sensitive_mutations_and_exports():
    owner = _signup_and_login("role-crm-owner@example.com", "Role CRM")
    viewer = _teammate_headers(owner, "viewer", "role-crm-viewer@example.com")
    support = _teammate_headers(owner, "support", "role-crm-support@example.com")
    marketer = _teammate_headers(owner, "marketer", "role-crm-marketer@example.com")
    manager = _teammate_headers(owner, "manager", "role-crm-manager@example.com")

    denied_segment = client.post("/v1/crm/segments", headers=viewer, json={"name": "Viewer segment"})
    assert denied_segment.status_code == 403
    assert client.get("/v1/crm/contacts", headers=viewer).status_code == 200

    created_segment = client.post("/v1/crm/segments", headers=marketer, json={"name": "New leads", "tag": "new"})
    assert created_segment.status_code == 201

    contact_id = _create_contact(owner, "crm-rbac")

    support_note = client.post(
        f"/v1/crm/contacts/{contact_id}/notes",
        headers=support,
        json={"text": "Call customer back"},
    )
    assert support_note.status_code == 201

    denied_consent = client.patch(
        f"/v1/crm/contacts/{contact_id}/consent",
        headers=marketer,
        json={"email_marketing": True, "sms_marketing": False},
    )
    assert denied_consent.status_code == 403

    support_consent = client.patch(
        f"/v1/crm/contacts/{contact_id}/consent",
        headers=support,
        json={"email_marketing": True, "sms_marketing": False},
    )
    assert support_consent.status_code == 200

    denied_campaign = client.post(
        "/v1/crm/campaigns/send",
        headers=support,
        json={"channel": "email", "subject": "Hello", "message": "Karibu"},
    )
    assert denied_campaign.status_code == 403

    marketer_campaign = client.post(
        "/v1/crm/campaigns/send",
        headers=marketer,
        json={"channel": "email", "subject": "Hello", "message": "Karibu"},
    )
    assert marketer_campaign.status_code == 201

    denied_export = client.get(f"/v1/crm/contacts/{contact_id}/export", headers=support)
    assert denied_export.status_code == 403

    manager_export = client.get(f"/v1/crm/contacts/{contact_id}/export", headers=manager)
    assert manager_export.status_code == 200


def test_payment_role_matrix_restricts_provider_refund_report_and_checkout_actions():
    owner = _signup_and_login("role-pay-owner@example.com", "Role Pay")
    viewer = _teammate_headers(owner, "viewer", "role-pay-viewer@example.com")
    support = _teammate_headers(owner, "support", "role-pay-support@example.com")
    manager = _teammate_headers(owner, "manager", "role-pay-manager@example.com")

    denied_provider = client.post(
        "/v1/payments/providers",
        headers=manager,
        json={"provider": "mpesa", "channel": "stk", "status": "active"},
    )
    assert denied_provider.status_code == 403

    owner_provider = client.post(
        "/v1/payments/providers",
        headers=owner,
        json={"provider": "mpesa", "channel": "stk", "status": "active"},
    )
    assert owner_provider.status_code == 201

    denied_checkout = client.post(
        "/v1/payments/mpesa/initiate",
        headers=viewer,
        json={"phone": "+254700123456", "amount": 1000, "currency": "KES", "reference": "VIEWER-ORDER"},
    )
    assert denied_checkout.status_code == 403
    assert client.get("/v1/payments/summary", headers=viewer).status_code == 200

    support_checkout = client.post(
        "/v1/payments/mpesa/initiate",
        headers=support,
        json={"phone": "+254700123456", "amount": 1000, "currency": "KES", "reference": "SUPPORT-ORDER"},
    )
    assert support_checkout.status_code == 201

    contact_id = _create_contact(owner, "pay-rbac")
    payment_id = _create_successful_payment(owner, "pay-rbac", contact_id=contact_id)

    denied_refund = client.post(
        f"/v1/payments/{payment_id}/refund",
        headers=support,
        json={"amount": 100, "reason": "Customer request"},
    )
    assert denied_refund.status_code == 403

    manager_refund = client.post(
        f"/v1/payments/{payment_id}/refund",
        headers=manager,
        json={"amount": 100, "reason": "Customer request"},
    )
    assert manager_refund.status_code == 201

    denied_report = client.get("/v1/payments/reports/monthly", headers=support)
    assert denied_report.status_code == 403

    manager_report = client.get("/v1/payments/reports/monthly", headers=manager)
    assert manager_report.status_code == 200


def test_whatsapp_role_matrix_restricts_faq_and_service_actions():
    owner = _signup_and_login("role-wa-owner@example.com", "Role WhatsApp")
    viewer = _teammate_headers(owner, "viewer", "role-wa-viewer@example.com")
    support = _teammate_headers(owner, "support", "role-wa-support@example.com")
    marketer = _teammate_headers(owner, "marketer", "role-wa-marketer@example.com")

    denied_faq = client.post(
        "/v1/whatsapp/faq",
        headers=support,
        json={"question": "Hours?", "answer": "We open at 9am."},
    )
    assert denied_faq.status_code == 403

    marketer_faq = client.post(
        "/v1/whatsapp/faq",
        headers=marketer,
        json={"question": "Hours?", "answer": "We open at 9am."},
    )
    assert marketer_faq.status_code == 201

    thread_id = _create_whatsapp_thread(owner, "wa-rbac")

    denied_reply = client.post(
        f"/v1/whatsapp/conversations/{thread_id}/reply-human",
        headers=viewer,
        json={"message": "Thanks for reaching out"},
    )
    assert denied_reply.status_code == 403
    assert client.get("/v1/whatsapp/conversations", headers=viewer).status_code == 200

    support_reply = client.post(
        f"/v1/whatsapp/conversations/{thread_id}/reply-human",
        headers=support,
        json={"message": "Thanks for reaching out"},
    )
    assert support_reply.status_code == 200
