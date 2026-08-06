from __future__ import annotations

import os


LOCAL_ENVIRONMENTS = {"dev", "development", "local", "test", "testing"}
MIN_PROTECTED_SECRET_LENGTH = 32
PLACEHOLDER_SECRETS = {
    "dev-mpesa-secret",
    "dev-whatsapp-secret",
    "replace-with-random-mpesa-webhook-secret",
    "replace-with-random-whatsapp-webhook-secret",
}


class WebhookSecretConfigurationError(RuntimeError):
    """Raised when a provider webhook secret is unavailable in a protected environment."""


def runtime_environment() -> str:
    configured = os.getenv("KAZIBOOST_ENV", "").strip().lower()
    if configured:
        return configured
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "test"
    return "production"


def protected_environment() -> bool:
    return runtime_environment() not in LOCAL_ENVIRONMENTS


def webhook_secret(env_var: str, dev_default: str, provider: str) -> str:
    environment = runtime_environment()
    configured = (os.getenv(env_var) or "").strip()

    if environment in LOCAL_ENVIRONMENTS:
        return configured or dev_default

    if (
        not configured
        or configured in PLACEHOLDER_SECRETS
        or len(configured) < MIN_PROTECTED_SECRET_LENGTH
    ):
        raise WebhookSecretConfigurationError(
            f"{provider} webhook secret is not configured for {environment}; set {env_var}"
        )

    return configured


def webhook_secret_checks() -> dict[str, str]:
    if not protected_environment():
        return {"mpesa_webhook_secret": "local-default", "whatsapp_webhook_secret": "local-default"}

    checks: dict[str, str] = {}
    for key, env_var, dev_default, provider in (
        ("mpesa_webhook_secret", "KAZIBOOST_MPESA_CALLBACK_SECRET", "dev-mpesa-secret", "M-Pesa"),
        (
            "whatsapp_webhook_secret",
            "KAZIBOOST_WHATSAPP_WEBHOOK_SECRET",
            "dev-whatsapp-secret",
            "WhatsApp",
        ),
    ):
        try:
            webhook_secret(env_var=env_var, dev_default=dev_default, provider=provider)
        except WebhookSecretConfigurationError:
            checks[key] = "missing"
        else:
            checks[key] = "ok"
    return checks


def webhook_secrets_ready() -> bool:
    return all(value != "missing" for value in webhook_secret_checks().values())
