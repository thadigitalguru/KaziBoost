from fastapi import APIRouter, Depends, Header, HTTPException, status

from .store import Tenant, User

from .models import AuthResponse, LoginRequest, SignUpRequest, SignUpResponse, TenantOut, UserOut
from .store import store


router = APIRouter(prefix="/v1/auth", tags=["auth"])


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


@router.get("/me")
def me(current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> dict:
    user, tenant = current
    return {"user": _user_out(user).model_dump(), "tenant": _tenant_out(tenant).model_dump()}
