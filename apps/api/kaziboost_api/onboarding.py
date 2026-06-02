from fastapi import APIRouter, Depends

from .auth import get_current_user_and_tenant
from .models import OnboardingChecklistResponse, OnboardingRecommendationsResponse
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/onboarding", tags=["onboarding"])


@router.get("/checklist", response_model=OnboardingChecklistResponse)
def checklist(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> OnboardingChecklistResponse:
    user, _tenant = current
    result = store.onboarding_checklist(tenant_id=user.tenant_id)
    return OnboardingChecklistResponse(**result)


@router.get("/recommendations", response_model=OnboardingRecommendationsResponse)
def recommendations(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> OnboardingRecommendationsResponse:
    user, _tenant = current
    items = store.onboarding_recommendations(tenant_id=user.tenant_id)
    return OnboardingRecommendationsResponse(total=len(items), items=items)
