from fastapi import APIRouter, Depends, HTTPException, status

from .auth import OWNER_ONLY, _tenant_out, _user_out, get_current_user_and_tenant, require_roles
from .models import TenantSettingsRequest, TenantSettingsResponse
from .store import User, Tenant, store


router = APIRouter(prefix="/v1/settings", tags=["settings"])


@router.get("/profile", response_model=TenantSettingsResponse)
def get_profile(current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> TenantSettingsResponse:
    user, tenant = current
    return TenantSettingsResponse(tenant=_tenant_out(tenant), user=_user_out(user))


@router.put("/profile", response_model=TenantSettingsResponse)
def update_profile(
    payload: TenantSettingsRequest,
    current: tuple[User, Tenant] = Depends(require_roles(*OWNER_ONLY)),
) -> TenantSettingsResponse:
    requester, tenant = current
    try:
        updated_tenant, updated_user = store.update_tenant_profile(
            tenant_id=tenant.id,
            user_id=requester.id,
            business_name=payload.business_name,
            owner_name=payload.owner_name,
            actor_user_id=requester.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return TenantSettingsResponse(tenant=_tenant_out(updated_tenant), user=_user_out(updated_user))
