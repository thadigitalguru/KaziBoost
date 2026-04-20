from fastapi import APIRouter, Depends, status

from .auth import get_current_user_and_tenant
from .models import (
    WhatsAppBotReplyResponse,
    WhatsAppConversationListResponse,
    WhatsAppConversationOut,
    WhatsAppFAQCreateRequest,
    WhatsAppHandoffRequest,
    WhatsAppIncomingRequest,
)
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/whatsapp", tags=["whatsapp"])


@router.post("/webhook/incoming", response_model=WhatsAppConversationOut, status_code=status.HTTP_201_CREATED)
def incoming_webhook(
    payload: WhatsAppIncomingRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppConversationOut:
    user, _tenant = current
    conversation = store.ingest_whatsapp_message(
        tenant_id=user.tenant_id,
        from_phone=payload.from_phone,
        message_text=payload.message_text,
        language=payload.language,
    )
    return WhatsAppConversationOut(
        thread_id=conversation.thread_id,
        from_phone=conversation.from_phone,
        status=conversation.status,
        last_message=conversation.last_message,
        assigned_to=conversation.assigned_to,
    )


@router.get("/conversations", response_model=WhatsAppConversationListResponse)
def list_conversations(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppConversationListResponse:
    user, _tenant = current
    conversations = store.list_whatsapp_conversations(tenant_id=user.tenant_id)
    items = [
        WhatsAppConversationOut(
            thread_id=item.thread_id,
            from_phone=item.from_phone,
            status=item.status,
            last_message=item.last_message,
            assigned_to=item.assigned_to,
        )
        for item in conversations
    ]
    return WhatsAppConversationListResponse(total=len(items), items=items)


@router.post("/faq", status_code=status.HTTP_201_CREATED)
def add_faq(
    payload: WhatsAppFAQCreateRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> dict:
    user, _tenant = current
    return store.add_whatsapp_faq(tenant_id=user.tenant_id, question=payload.question, answer=payload.answer)


@router.post("/conversations/{thread_id}/reply-bot", response_model=WhatsAppBotReplyResponse)
def bot_reply(
    thread_id: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppBotReplyResponse:
    user, _tenant = current
    reply = store.whatsapp_bot_reply(tenant_id=user.tenant_id, thread_id=thread_id)
    return WhatsAppBotReplyResponse(**reply)


@router.post("/conversations/{thread_id}/handoff", response_model=WhatsAppConversationOut)
def handoff(
    thread_id: str,
    payload: WhatsAppHandoffRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppConversationOut:
    user, _tenant = current
    conversation = store.whatsapp_handoff(tenant_id=user.tenant_id, thread_id=thread_id, assigned_to=payload.assigned_to)
    return WhatsAppConversationOut(
        thread_id=conversation.thread_id,
        from_phone=conversation.from_phone,
        status=conversation.status,
        last_message=conversation.last_message,
        assigned_to=conversation.assigned_to,
    )
