from __future__ import annotations

import hashlib
import hmac

from .webhook_secrets import webhook_secret


def _secret() -> str:
    return webhook_secret(
        env_var="KAZIBOOST_MPESA_CALLBACK_SECRET",
        dev_default="dev-mpesa-secret",
        provider="M-Pesa",
    )


def build_mpesa_callback_signature(payment_id: str, provider_tx_id: str, status: str) -> str:
    payload = f"{payment_id}:{provider_tx_id}:{status}".encode("utf-8")
    return hmac.new(_secret().encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_mpesa_callback_signature(signature: str, payment_id: str, provider_tx_id: str, status: str) -> bool:
    expected = build_mpesa_callback_signature(payment_id=payment_id, provider_tx_id=provider_tx_id, status=status)
    return hmac.compare_digest(signature, expected)
