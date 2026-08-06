import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from kaziboost_api.main import app
from kaziboost_api.payments_security import build_mpesa_callback_signature, verify_mpesa_callback_signature
from kaziboost_api.webhook_secrets import WebhookSecretConfigurationError
from kaziboost_api.whatsapp_security import build_whatsapp_signature, verify_whatsapp_signature


client = TestClient(app)


def _hmac_sha256(secret: str, payload: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


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


def test_local_mode_uses_deterministic_webhook_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KAZIBOOST_ENV", "local")
    monkeypatch.delenv("KAZIBOOST_MPESA_CALLBACK_SECRET", raising=False)
    monkeypatch.delenv("KAZIBOOST_WHATSAPP_WEBHOOK_SECRET", raising=False)

    mpesa_signature = build_mpesa_callback_signature("payment-1", "tx-1", "success")
    whatsapp_signature = build_whatsapp_signature("evt-1", "+254700123456", "Hello", "en")

    assert verify_mpesa_callback_signature(mpesa_signature, "payment-1", "tx-1", "success") is True
    assert verify_whatsapp_signature(whatsapp_signature, "evt-1", "+254700123456", "Hello", "en") is True


def test_local_mode_allows_configured_webhook_secrets(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KAZIBOOST_ENV", "local")
    monkeypatch.setenv("KAZIBOOST_MPESA_CALLBACK_SECRET", "local-mpesa")
    monkeypatch.setenv("KAZIBOOST_WHATSAPP_WEBHOOK_SECRET", "local-whatsapp")

    mpesa_signature = build_mpesa_callback_signature("payment-1", "tx-1", "success")
    whatsapp_signature = build_whatsapp_signature("evt-1", "+254700123456", "Hello", "en")

    assert mpesa_signature == _hmac_sha256("local-mpesa", "payment-1:tx-1:success")
    assert whatsapp_signature == _hmac_sha256("local-whatsapp", "evt-1:+254700123456:Hello:en")


def test_production_mode_requires_configured_webhook_secrets(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KAZIBOOST_ENV", "production")
    monkeypatch.delenv("KAZIBOOST_MPESA_CALLBACK_SECRET", raising=False)
    monkeypatch.delenv("KAZIBOOST_WHATSAPP_WEBHOOK_SECRET", raising=False)

    with pytest.raises(WebhookSecretConfigurationError, match="KAZIBOOST_MPESA_CALLBACK_SECRET"):
        build_mpesa_callback_signature("payment-1", "tx-1", "success")

    with pytest.raises(WebhookSecretConfigurationError, match="KAZIBOOST_WHATSAPP_WEBHOOK_SECRET"):
        build_whatsapp_signature("evt-1", "+254700123456", "Hello", "en")


@pytest.mark.parametrize(
    "mpesa_secret,whatsapp_secret",
    [
        ("replace-with-random-mpesa-webhook-secret", "replace-with-random-whatsapp-webhook-secret"),
        ("dev-mpesa-secret", "dev-whatsapp-secret"),
        ("   ", "   "),
        ("short-mpesa-secret", "short-whatsapp-secret"),
    ],
)
def test_production_mode_rejects_placeholder_or_weak_webhook_secrets(
    monkeypatch: pytest.MonkeyPatch,
    mpesa_secret: str,
    whatsapp_secret: str,
):
    monkeypatch.setenv("KAZIBOOST_ENV", "production")
    monkeypatch.setenv("KAZIBOOST_MPESA_CALLBACK_SECRET", mpesa_secret)
    monkeypatch.setenv("KAZIBOOST_WHATSAPP_WEBHOOK_SECRET", whatsapp_secret)

    with pytest.raises(WebhookSecretConfigurationError):
        build_mpesa_callback_signature("payment-1", "tx-1", "success")

    with pytest.raises(WebhookSecretConfigurationError):
        build_whatsapp_signature("evt-1", "+254700123456", "Hello", "en")


def test_production_mode_uses_configured_webhook_secrets(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KAZIBOOST_ENV", "production")
    monkeypatch.setenv("KAZIBOOST_MPESA_CALLBACK_SECRET", "configured-mpesa-secret-with-32-plus-chars")
    monkeypatch.setenv("KAZIBOOST_WHATSAPP_WEBHOOK_SECRET", "configured-whatsapp-secret-with-32-plus-chars")

    mpesa_signature = build_mpesa_callback_signature("payment-1", "tx-1", "success")
    whatsapp_signature = build_whatsapp_signature("evt-1", "+254700123456", "Hello", "en")
    dev_mpesa_signature = _hmac_sha256("dev-mpesa-secret", "payment-1:tx-1:success")
    dev_whatsapp_signature = _hmac_sha256("dev-whatsapp-secret", "evt-1:+254700123456:Hello:en")

    assert mpesa_signature == _hmac_sha256(
        "configured-mpesa-secret-with-32-plus-chars",
        "payment-1:tx-1:success",
    )
    assert whatsapp_signature == _hmac_sha256(
        "configured-whatsapp-secret-with-32-plus-chars",
        "evt-1:+254700123456:Hello:en",
    )
    assert verify_mpesa_callback_signature(mpesa_signature, "payment-1", "tx-1", "success") is True
    assert verify_whatsapp_signature(whatsapp_signature, "evt-1", "+254700123456", "Hello", "en") is True
    assert verify_mpesa_callback_signature(dev_mpesa_signature, "payment-1", "tx-1", "success") is False
    assert verify_whatsapp_signature(dev_whatsapp_signature, "evt-1", "+254700123456", "Hello", "en") is False


def test_webhook_routes_fail_closed_when_production_secret_is_missing(monkeypatch: pytest.MonkeyPatch):
    headers = _auth_headers("webhooksecret@example.com", "Webhook Secret Shop")
    payment = client.post(
        "/v1/payments/mpesa/initiate",
        headers=headers,
        json={"phone": "+254700123456", "amount": 1000, "currency": "KES", "reference": "SECRET-ORDER"},
    )
    assert payment.status_code == 201

    monkeypatch.setenv("KAZIBOOST_ENV", "production")
    monkeypatch.delenv("KAZIBOOST_MPESA_CALLBACK_SECRET", raising=False)
    monkeypatch.delenv("KAZIBOOST_WHATSAPP_WEBHOOK_SECRET", raising=False)

    payment_callback = client.post(
        "/v1/payments/mpesa/callback",
        headers={**headers, "x-callback-signature": "placeholder-signature"},
        json={
            "payment_id": payment.json()["payment_id"],
            "provider_tx_id": "TX-MISSING-SECRET",
            "status": "success",
        },
    )
    assert payment_callback.status_code == 503
    assert payment_callback.json()["detail"] == "Webhook verification is temporarily unavailable"

    whatsapp_callback = client.post(
        "/v1/whatsapp/webhook/incoming",
        headers={**headers, "x-event-id": "evt-missing-secret", "x-webhook-signature": "placeholder-signature"},
        json={"from_phone": "+254700999888", "message_text": "Need pricing", "language": "en"},
    )
    assert whatsapp_callback.status_code == 503
    assert whatsapp_callback.json()["detail"] == "Webhook verification is temporarily unavailable"


def test_readiness_reports_missing_protected_webhook_secrets_without_values(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KAZIBOOST_ENV", "staging")
    monkeypatch.delenv("KAZIBOOST_MPESA_CALLBACK_SECRET", raising=False)
    monkeypatch.delenv("KAZIBOOST_WHATSAPP_WEBHOOK_SECRET", raising=False)

    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["mpesa_webhook_secret"] == "missing"
    assert body["checks"]["whatsapp_webhook_secret"] == "missing"
    assert "KAZIBOOST_MPESA_CALLBACK_SECRET" not in response.text
    assert "KAZIBOOST_WHATSAPP_WEBHOOK_SECRET" not in response.text


def test_readiness_accepts_configured_protected_webhook_secrets(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KAZIBOOST_ENV", "production")
    monkeypatch.setenv("KAZIBOOST_MPESA_CALLBACK_SECRET", "configured-mpesa-secret-with-32-plus-chars")
    monkeypatch.setenv("KAZIBOOST_WHATSAPP_WEBHOOK_SECRET", "configured-whatsapp-secret-with-32-plus-chars")

    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["mpesa_webhook_secret"] == "ok"
    assert body["checks"]["whatsapp_webhook_secret"] == "ok"
