from __future__ import annotations

import hashlib
import hmac
import os


def _secret() -> str:
    return os.getenv("KAZIBOOST_WHATSAPP_WEBHOOK_SECRET", "dev-whatsapp-secret")


def build_whatsapp_signature(event_id: str, from_phone: str, message_text: str, language: str) -> str:
    payload = f"{event_id}:{from_phone}:{message_text}:{language}".encode("utf-8")
    return hmac.new(_secret().encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_whatsapp_signature(signature: str, event_id: str, from_phone: str, message_text: str, language: str) -> bool:
    expected = build_whatsapp_signature(
        event_id=event_id,
        from_phone=from_phone,
        message_text=message_text,
        language=language,
    )
    return hmac.compare_digest(signature, expected)
