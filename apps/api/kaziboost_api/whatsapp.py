from fastapi import APIRouter, Depends, status

from .auth import get_current_user_and_tenant
from .models import WhatsAppConversationListResponse, WhatsAppConversationOut, WhatsAppIncomingRequest
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
