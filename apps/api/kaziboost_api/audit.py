from fastapi import APIRouter, Depends, Query

from .auth import get_current_user_and_tenant
from .models import AuditEventListResponse, AuditEventOut
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/audit", tags=["audit"])


@router.get("/events", response_model=AuditEventListResponse)
def list_events(
    limit: int = Query(default=100, ge=1, le=500),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> AuditEventListResponse:
    user, _tenant = current
    events = store.list_audit_events(tenant_id=user.tenant_id, limit=limit)
    items = [
        AuditEventOut(
            id=event.id,
            event_type=event.event_type,
            actor_user_id=event.actor_user_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            metadata=event.metadata,
            created_at=event.created_at,
        )
        for event in events
    ]
    return AuditEventListResponse(total=len(items), items=items)
