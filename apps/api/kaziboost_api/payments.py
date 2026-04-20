from fastapi import APIRouter, Depends, HTTPException, status

from .auth import get_current_user_and_tenant
from .models import MpesaInitiateRequest, PaymentOut
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/payments", tags=["payments"])


def _payment_out(payment) -> PaymentOut:
    return PaymentOut(
        payment_id=payment.payment_id,
        provider=payment.provider,
        phone=payment.phone,
        amount=payment.amount,
        currency=payment.currency,
        reference=payment.reference,
        status=payment.status,
    )


@router.post("/mpesa/initiate", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def initiate_mpesa(
    payload: MpesaInitiateRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> PaymentOut:
    user, _tenant = current
    payment = store.initiate_mpesa_payment(
        tenant_id=user.tenant_id,
        phone=payload.phone,
        amount=payload.amount,
        currency=payload.currency,
        reference=payload.reference,
    )
    return _payment_out(payment)


@router.get("/{payment_id}", response_model=PaymentOut)
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
