from fastapi import APIRouter, Depends, HTTPException, status

from .auth import get_current_user_and_tenant
from .contracts import error_responses
from .models import MpesaCallbackRequest, MpesaCallbackResponse, MpesaInitiateRequest, PaymentListResponse, PaymentOut
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/payments", tags=["payments"])


def _validate_mpesa_input(phone: str, currency: str) -> None:
    if currency.upper() != "KES":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="M-Pesa only supports KES")
    if not phone.startswith("+254"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="M-Pesa phone must use Kenyan +254 format")


def _payment_out(payment) -> PaymentOut:
    return PaymentOut(
        payment_id=payment.payment_id,
        provider=payment.provider,
        phone=payment.phone,
        amount=payment.amount,
        currency=payment.currency,
        reference=payment.reference,
        status=payment.status,
        contact_id=payment.contact_id,
        provider_tx_id=payment.provider_tx_id,
    )


@router.post(
    "/mpesa/initiate",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(400, 401, 429),
)
def initiate_mpesa(
    payload: MpesaInitiateRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> PaymentOut:
    user, _tenant = current
    _validate_mpesa_input(phone=payload.phone, currency=payload.currency)
    payment = store.initiate_mpesa_payment(
        tenant_id=user.tenant_id,
        phone=payload.phone,
        amount=payload.amount,
        currency=payload.currency,
        reference=payload.reference,
        contact_id=payload.contact_id,
    )
    return _payment_out(payment)


@router.post("/mpesa/callback", response_model=MpesaCallbackResponse, responses=error_responses(400, 401, 404))
def mpesa_callback(
    payload: MpesaCallbackRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> MpesaCallbackResponse:
    user, _tenant = current
    if payload.status not in {"success", "failed", "pending"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment callback status")
    try:
        result = store.apply_mpesa_callback(
            tenant_id=user.tenant_id,
            payment_id=payload.payment_id,
            provider_tx_id=payload.provider_tx_id,
            status=payload.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return MpesaCallbackResponse(
        payment_id=payload.payment_id,
        idempotent=bool(result["idempotent"]),
        status=result["payment"].status,
    )


@router.get("/reconciliation", response_model=PaymentListResponse, responses=error_responses(401))
def reconciliation(
    contact_id: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> PaymentListResponse:
    user, _tenant = current
    items = store.list_payments_by_contact(tenant_id=user.tenant_id, contact_id=contact_id)
    return PaymentListResponse(total=len(items), items=[_payment_out(item) for item in items])


@router.get("/{payment_id}", response_model=PaymentOut, responses=error_responses(401, 404))
def get_payment(
    payment_id: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> PaymentOut:
    user, _tenant = current
    try:
        payment = store.get_payment(tenant_id=user.tenant_id, payment_id=payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _payment_out(payment)
