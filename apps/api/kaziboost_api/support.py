from fastapi import APIRouter, Depends

from .auth import get_current_user_and_tenant
from .models import SupportFeedbackRequest, SupportFeedbackResponse
from .store import User, Tenant, store


router = APIRouter(prefix="/v1/support", tags=["support"])


@router.post("/feedback", response_model=SupportFeedbackResponse)
def submit_feedback(
    payload: SupportFeedbackRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> SupportFeedbackResponse:
    user, tenant = current
    feedback_id = f"feedback-{len(store.list_audit_events(tenant_id=tenant.id, entity_type='feedback', limit=1000)) + 1}"
    store.record_audit_event(
        tenant_id=tenant.id,
        event_type="feedback.submitted",
        entity_type="feedback",
        entity_id=feedback_id,
        actor_user_id=user.id,
        metadata={"page": payload.page, "message": payload.message[:240]},
    )
    return SupportFeedbackResponse(status="received", feedback_id=feedback_id)
