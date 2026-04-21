from __future__ import annotations

import hashlib
import hmac
import os


def _secret() -> str:
    return os.getenv("KAZIBOOST_MPESA_CALLBACK_SECRET", "dev-mpesa-secret")


def build_mpesa_callback_signature(payment_id: str, provider_tx_id: str, status: str) -> str:
    payload = f"{payment_id}:{provider_tx_id}:{status}".encode("utf-8")
    return hmac.new(_secret().encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_mpesa_callback_signature(signature: str, payment_id: str, provider_tx_id: str, status: str) -> bool:
    expected = build_mpesa_callback_signature(payment_id=payment_id, provider_tx_id=provider_tx_id, status=status)
    return hmac.compare_digest(signature, expected)
