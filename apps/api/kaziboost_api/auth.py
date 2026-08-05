from fastapi import APIRouter, Depends, Header, HTTPException, status

from .store import Tenant, User

from .models import (
    AuthResponse,
    CreateTeammateRequest,
    LoginRequest,
    MFAChallengeResponse,
    MFAEnrollResponse,
    MFAVerifyRequest,
    MFAVerifyResponse,
    SignUpRequest,
    SignUpResponse,
    TenantOut,
    UpdateRoleRequest,
    UserOut,
)
from .store import store


router = APIRouter(prefix="/v1/auth", tags=["auth"])

ROLE_OWNER = "owner"
ROLE_MANAGER = "manager"
ROLE_MARKETER = "marketer"
ROLE_SUPPORT = "support"

OWNER_ONLY = (ROLE_OWNER,)
SITE_CONTENT_ROLES = (ROLE_OWNER, ROLE_MANAGER, ROLE_MARKETER)
SITE_ADMIN_ROLES = (ROLE_OWNER, ROLE_MANAGER)
CRM_FORM_SEGMENT_ROLES = (ROLE_OWNER, ROLE_MANAGER, ROLE_MARKETER)
CRM_SUPPORT_NOTE_ROLES = (ROLE_OWNER, ROLE_MANAGER, ROLE_MARKETER, ROLE_SUPPORT)
CRM_CONSENT_ROLES = (ROLE_OWNER, ROLE_MANAGER, ROLE_SUPPORT)
CRM_CAMPAIGN_ROLES = (ROLE_OWNER, ROLE_MANAGER, ROLE_MARKETER)
CRM_PRIVACY_EXPORT_ROLES = (ROLE_OWNER, ROLE_MANAGER)
PAYMENT_CHECKOUT_ROLES = (ROLE_OWNER, ROLE_MANAGER, ROLE_SUPPORT)
PAYMENT_PROVIDER_SETUP_ROLES = OWNER_ONLY
PAYMENT_REFUND_ROLES = (ROLE_OWNER, ROLE_MANAGER)
PAYMENT_REPORT_ROLES = (ROLE_OWNER, ROLE_MANAGER)
WHATSAPP_FAQ_CONTENT_ROLES = (ROLE_OWNER, ROLE_MANAGER, ROLE_MARKETER)
WHATSAPP_SERVICE_ACTION_ROLES = (ROLE_OWNER, ROLE_MANAGER, ROLE_SUPPORT)


def _user_out(user) -> UserOut:
    return UserOut(
        id=user.id,
        tenant_id=user.tenant_id,
        owner_name=user.owner_name,
        email=user.email,
        role=user.role,
    )


def _tenant_out(tenant) -> TenantOut:
    return TenantOut(id=tenant.id, name=tenant.name)


@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpRequest) -> SignUpResponse:
    try:
        tenant, user = store.create_tenant_and_owner(
            business_name=payload.business_name,
            owner_name=payload.owner_name,
            email=payload.email,
            password=payload.password,
        )
    except ValueError as exc:
        message = str(exc)
        if "already exists" in message.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    return SignUpResponse(user=_user_out(user), tenant=_tenant_out(tenant))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    try:
        result = store.authenticate(payload.email, payload.password)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, user, tenant = result
    return AuthResponse(access_token=token, user=_user_out(user), tenant=_tenant_out(tenant))


def _require_bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    return token


def get_current_user_and_tenant(token: str = Depends(_require_bearer_token)) -> tuple[User, Tenant]:
    try:
        resolved = store.resolve_token(token)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if not resolved:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return resolved


def require_roles(*allowed_roles: str):
    allowed = frozenset(allowed_roles)

    def _dependency(current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> tuple[User, Tenant]:
        user, _tenant = current
        if user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current

    return _dependency


@router.post("/teammates", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
def create_teammate(
    payload: CreateTeammateRequest,
    current: tuple[User, Tenant] = Depends(require_roles(*OWNER_ONLY)),
) -> SignUpResponse:
    requester, tenant = current
    try:
        user = store.create_teammate(
            tenant_id=tenant.id,
            owner_name=payload.owner_name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            actor_user_id=requester.id,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_409_CONFLICT if "exists" in message.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc

    return SignUpResponse(user=_user_out(user), tenant=_tenant_out(tenant))


@router.patch("/users/{user_id}/role", response_model=SignUpResponse)
def update_role(
    user_id: str,
    payload: UpdateRoleRequest,
    current: tuple[User, Tenant] = Depends(require_roles(*OWNER_ONLY)),
) -> SignUpResponse:
    requester, tenant = current
    try:
        user = store.update_user_role(
            tenant_id=tenant.id,
            user_id=user_id,
            role=payload.role,
            actor_user_id=requester.id,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "not found" in message.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc

    return SignUpResponse(user=_user_out(user), tenant=_tenant_out(tenant))


@router.post("/mfa/enroll", response_model=MFAEnrollResponse, status_code=status.HTTP_201_CREATED)
def enroll_mfa(current: tuple[User, Tenant] = Depends(require_roles(*OWNER_ONLY))) -> MFAEnrollResponse:
    user, _tenant = current
    payload = store.enroll_mfa(user_id=user.id)
    return MFAEnrollResponse(**payload)


@router.post("/mfa/challenge", response_model=MFAChallengeResponse, status_code=status.HTTP_201_CREATED)
def create_mfa_challenge(current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> MFAChallengeResponse:
    user, _tenant = current
    try:
        challenge = store.create_mfa_challenge(user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MFAChallengeResponse(
        challenge_id=challenge["challenge_id"],
        status=challenge["status"],
        test_code=challenge["code"],
    )


@router.post("/mfa/verify", response_model=MFAVerifyResponse)
def verify_mfa(
    payload: MFAVerifyRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> MFAVerifyResponse:
    user, _tenant = current
    try:
        challenge = store.verify_mfa_challenge(user_id=user.id, challenge_id=payload.challenge_id, code=payload.code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MFAVerifyResponse(challenge_id=challenge["challenge_id"], status=challenge["status"])


@router.post("/logout")
def logout(token: str = Depends(_require_bearer_token)) -> dict:
    store.revoke_token(token)
    return {"status": "logged_out"}


@router.get("/me")
def me(current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> dict:
    user, tenant = current
    return {"user": _user_out(user).model_dump(), "tenant": _tenant_out(tenant).model_dump()}
