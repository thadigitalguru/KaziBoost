from __future__ import annotations

import hashlib
import hmac

from .webhook_secrets import webhook_secret


def _secret() -> str:
    return webhook_secret(
        env_var="KAZIBOOST_WHATSAPP_WEBHOOK_SECRET",
        dev_default="dev-whatsapp-secret",
        provider="WhatsApp",
    )


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
