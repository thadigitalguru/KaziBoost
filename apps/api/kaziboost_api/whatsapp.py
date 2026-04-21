from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status

from .auth import get_current_user_and_tenant
from .models import (
    WhatsAppBotReplyResponse,
    WhatsAppConversationListResponse,
    WhatsAppConversationOut,
    WhatsAppFAQCreateRequest,
    WhatsAppHandoffRequest,
    WhatsAppIncomingRequest,
    WhatsAppReminderListResponse,
    WhatsAppReminderOut,
    WhatsAppReminderRequest,
)
from .store import Tenant, User, store
from .whatsapp_security import verify_whatsapp_signature


router = APIRouter(prefix="/v1/whatsapp", tags=["whatsapp"])


@router.post(
    "/webhook/incoming",
    response_model=WhatsAppConversationOut,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "booking_query": {
                            "summary": "Customer booking inquiry",
                            "value": {
                                "from_phone": "+254700333111",
                                "message_text": "Hi, I want to book a salon slot",
                                "language": "en",
                            },
                        }
                    }
                }
            }
        }
    },
)
def incoming_webhook(
    payload: WhatsAppIncomingRequest,
    response: Response,
    x_event_id: str = Header(alias="x-event-id"),
    x_webhook_signature: str = Header(alias="x-webhook-signature"),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppConversationOut:
    if not verify_whatsapp_signature(
        signature=x_webhook_signature,
        event_id=x_event_id,
        from_phone=payload.from_phone,
        message_text=payload.message_text,
        language=payload.language,
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    user, _tenant = current
    conversation, idempotent = store.ingest_whatsapp_message(
        tenant_id=user.tenant_id,
        from_phone=payload.from_phone,
        message_text=payload.message_text,
        language=payload.language,
        event_id=x_event_id,
    )
    if idempotent:
        response.status_code = status.HTTP_200_OK

    return WhatsAppConversationOut(
        thread_id=conversation.thread_id,
        from_phone=conversation.from_phone,
        status=conversation.status,
        last_message=conversation.last_message,
        assigned_to=conversation.assigned_to,
        idempotent=idempotent,
    )


@router.get("/conversations", response_model=WhatsAppConversationListResponse)
def list_conversations(
    status: str | None = Query(default=None),
    assigned_to: str | None = Query(default=None),
    from_phone: str | None = Query(default=None),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppConversationListResponse:
    user, _tenant = current
    conversations = store.list_whatsapp_conversations(
        tenant_id=user.tenant_id,
        status=status,
        assigned_to=assigned_to,
        from_phone=from_phone,
    )
    items = [
        WhatsAppConversationOut(
            thread_id=item.thread_id,
            from_phone=item.from_phone,
            status=item.status,
            last_message=item.last_message,
            assigned_to=item.assigned_to,
            idempotent=False,
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


@router.get("/faq")
def list_faq(current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> dict:
    user, _tenant = current
    items = store.list_whatsapp_faq(tenant_id=user.tenant_id)
    return {"total": len(items), "items": items}


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
        idempotent=False,
    )


@router.patch("/conversations/{thread_id}/assign", response_model=WhatsAppConversationOut)
def assign_conversation(
    thread_id: str,
    payload: WhatsAppHandoffRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppConversationOut:
    user, _tenant = current
    try:
        conversation = store.whatsapp_assign(tenant_id=user.tenant_id, thread_id=thread_id, assigned_to=payload.assigned_to)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return WhatsAppConversationOut(
        thread_id=conversation.thread_id,
        from_phone=conversation.from_phone,
        status=conversation.status,
        last_message=conversation.last_message,
        assigned_to=conversation.assigned_to,
        idempotent=False,
    )


@router.post("/conversations/{thread_id}/close", response_model=WhatsAppConversationOut)
def close_conversation(
    thread_id: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppConversationOut:
    user, _tenant = current
    try:
        conversation = store.set_whatsapp_status(tenant_id=user.tenant_id, thread_id=thread_id, status="closed")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return WhatsAppConversationOut(
        thread_id=conversation.thread_id,
        from_phone=conversation.from_phone,
        status=conversation.status,
        last_message=conversation.last_message,
        assigned_to=conversation.assigned_to,
        idempotent=False,
    )


@router.post("/conversations/{thread_id}/reopen", response_model=WhatsAppConversationOut)
def reopen_conversation(
    thread_id: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppConversationOut:
    user, _tenant = current
    try:
        conversation = store.set_whatsapp_status(tenant_id=user.tenant_id, thread_id=thread_id, status="open")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return WhatsAppConversationOut(
        thread_id=conversation.thread_id,
        from_phone=conversation.from_phone,
        status=conversation.status,
        last_message=conversation.last_message,
        assigned_to=conversation.assigned_to,
        idempotent=False,
    )


@router.post("/conversations/{thread_id}/remind", response_model=WhatsAppReminderOut, status_code=status.HTTP_201_CREATED)
def schedule_reminder(
    thread_id: str,
    payload: WhatsAppReminderRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppReminderOut:
    user, _tenant = current
    try:
        reminder = store.schedule_whatsapp_reminder(tenant_id=user.tenant_id, thread_id=thread_id, message=payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return WhatsAppReminderOut(
        id=reminder.id,
        thread_id=reminder.thread_id,
        message=reminder.message,
        status=reminder.status,
        created_at=reminder.created_at,
    )


@router.get("/reminders/history", response_model=WhatsAppReminderListResponse)
def reminder_history(
    status: str | None = Query(default=None),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppReminderListResponse:
    user, _tenant = current
    items = [
        WhatsAppReminderOut(
            id=item.id,
            thread_id=item.thread_id,
            message=item.message,
            status=item.status,
            created_at=item.created_at,
        )
        for item in store.list_whatsapp_reminders(tenant_id=user.tenant_id, status=status)
    ]
    return WhatsAppReminderListResponse(total=len(items), items=items)


@router.patch("/reminders/{reminder_id}/sent", response_model=WhatsAppReminderOut)
def mark_reminder_sent(
    reminder_id: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppReminderOut:
    user, _tenant = current
    try:
        item = store.mark_whatsapp_reminder_sent(tenant_id=user.tenant_id, reminder_id=reminder_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return WhatsAppReminderOut(
        id=item.id,
        thread_id=item.thread_id,
        message=item.message,
        status=item.status,
        created_at=item.created_at,
    )


@router.get("/queue/overdue", response_model=WhatsAppConversationListResponse)
def overdue_queue(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> WhatsAppConversationListResponse:
    user, _tenant = current
    items = [
        WhatsAppConversationOut(
            thread_id=item.thread_id,
            from_phone=item.from_phone,
            status=item.status,
            last_message=item.last_message,
            assigned_to=item.assigned_to,
            idempotent=False,
        )
        for item in store.overdue_whatsapp_queue(tenant_id=user.tenant_id)
    ]
    return WhatsAppConversationListResponse(total=len(items), items=items)


@router.get("/stats/sla")
def sla_stats(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> dict:
    user, _tenant = current
    return store.whatsapp_sla_stats(tenant_id=user.tenant_id)
