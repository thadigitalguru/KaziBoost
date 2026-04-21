from fastapi import APIRouter, Depends

from .auth import get_current_user_and_tenant
from .models import OnboardingChecklistResponse
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/onboarding", tags=["onboarding"])


@router.get("/checklist", response_model=OnboardingChecklistResponse)
def checklist(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> OnboardingChecklistResponse:
    user, _tenant = current
    result = store.onboarding_checklist(tenant_id=user.tenant_id)
    return OnboardingChecklistResponse(**result)
