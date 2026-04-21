from fastapi import APIRouter, Depends, Header, HTTPException, status

from .auth import get_current_user_and_tenant
from .contracts import error_responses
from .models import (
    MpesaCallbackRequest,
    MpesaCallbackResponse,
    MpesaInitiateRequest,
    PaymentListResponse,
    PaymentOut,
    PaymentsMonthlyReportResponse,
    PaymentsSummaryResponse,
    RefundListResponse,
    RefundReportResponse,
    RefundOut,
    RefundRequest,
)
from .store import Tenant, User, store
from .payments_security import verify_mpesa_callback_signature


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
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "basic": {
                            "summary": "Basic M-Pesa checkout",
                            "value": {
                                "phone": "+254700123456",
                                "amount": 1500,
                                "currency": "KES",
                                "reference": "BOOKING-001",
                            },
                        }
                    }
                }
            }
        }
    },
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
    x_callback_signature: str = Header(alias="x-callback-signature"),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> MpesaCallbackResponse:
    user, _tenant = current
    if payload.status not in {"success", "failed", "pending"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment callback status")
    if not verify_mpesa_callback_signature(
        signature=x_callback_signature,
        payment_id=payload.payment_id,
        provider_tx_id=payload.provider_tx_id,
        status=payload.status,
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid callback signature")

    try:
        result = store.apply_mpesa_callback(
            tenant_id=user.tenant_id,
            payment_id=payload.payment_id,
            provider_tx_id=payload.provider_tx_id,
            status=payload.status,
            actor_user_id=user.id,
        )
    except ValueError as exc:
        if "state transition" in str(exc).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
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


@router.post("/{payment_id}/refund", response_model=RefundOut, status_code=status.HTTP_201_CREATED)
def create_refund(
    payment_id: str,
    payload: RefundRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> RefundOut:
    user, _tenant = current
    try:
        refund = store.create_refund(
            tenant_id=user.tenant_id,
            payment_id=payment_id,
            amount=payload.amount,
            reason=payload.reason,
            actor_user_id=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RefundOut(
        refund_id=refund.refund_id,
        payment_id=refund.payment_id,
        amount=refund.amount,
        reason=refund.reason,
        status=refund.status,
    )


@router.get("/{payment_id}/refunds", response_model=RefundListResponse)
def list_refunds(
    payment_id: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> RefundListResponse:
    user, _tenant = current
    try:
        refunds = store.list_refunds(tenant_id=user.tenant_id, payment_id=payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    items = [
        RefundOut(
            refund_id=refund.refund_id,
            payment_id=refund.payment_id,
            amount=refund.amount,
            reason=refund.reason,
            status=refund.status,
        )
        for refund in refunds
    ]
    return RefundListResponse(total=len(items), items=items)


@router.get("/summary", response_model=PaymentsSummaryResponse)
def payments_summary(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> PaymentsSummaryResponse:
    user, _tenant = current
    return PaymentsSummaryResponse(**store.payments_summary(tenant_id=user.tenant_id))


@router.get("/reports/monthly", response_model=PaymentsMonthlyReportResponse)
def monthly_report(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> PaymentsMonthlyReportResponse:
    user, _tenant = current
    return PaymentsMonthlyReportResponse(**store.payments_monthly_report(tenant_id=user.tenant_id))


@router.get("/refunds/report", response_model=RefundReportResponse)
def refund_report(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> RefundReportResponse:
    user, _tenant = current
    return RefundReportResponse(**store.refunds_report(tenant_id=user.tenant_id))


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
