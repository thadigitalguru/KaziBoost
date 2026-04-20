from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from .auth import get_current_user_and_tenant
from .models import (
    CRMFormCreateRequest,
    CRMFormOut,
    ContactListResponse,
    ContactOut,
    LeadSubmissionOut,
    LeadSubmitRequest,
)
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/crm", tags=["crm"])


def _contact_out(contact) -> ContactOut:
    return ContactOut(
        id=contact.id,
        name=contact.name,
        phone=contact.phone,
        email=contact.email,
        source=contact.source,
        tags=contact.tags,
    )


@router.post("/forms", response_model=CRMFormOut, status_code=status.HTTP_201_CREATED)
def create_form(payload: CRMFormCreateRequest, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> CRMFormOut:
    user, _ = current
    form = store.create_crm_form(
        tenant_id=user.tenant_id,
        name=payload.name,
        kind=payload.kind,
        fields=payload.fields,
    )
    return CRMFormOut(id=form.id, name=form.name, kind=form.kind, fields=form.fields)


@router.post("/forms/{form_id}/submit", response_model=LeadSubmissionOut, status_code=status.HTTP_201_CREATED)
def submit_form(
    form_id: str,
    payload: LeadSubmitRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> LeadSubmissionOut:
    user, _ = current
    try:
        interaction, contact = store.submit_form(
            tenant_id=user.tenant_id,
            form_id=form_id,
            name=payload.name,
            phone=payload.phone,
            email=payload.email,
            message=payload.message,
            source=payload.source,
            tags=payload.tags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return LeadSubmissionOut(
        id=interaction.id,
        form_id=form_id,
        source=interaction.source,
        message=interaction.message,
        contact=_contact_out(contact),
    )


@router.get("/contacts", response_model=ContactListResponse)
def list_contacts(
    source: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> ContactListResponse:
    user, _ = current
    items = store.list_contacts(tenant_id=user.tenant_id, source=source, tag=tag)
    response_items = [_contact_out(contact) for contact in items]
    return ContactListResponse(total=len(response_items), items=response_items)


@router.get("/contacts/export.csv")
def export_contacts_csv(
    source: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> Response:
    user, _ = current
    csv_data = store.export_contacts_csv(tenant_id=user.tenant_id, source=source, tag=tag)
    return Response(content=csv_data, media_type="text/csv")


@router.get("/contacts/{contact_id}/timeline")
def contact_timeline(contact_id: str, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> dict:
    user, _ = current
    try:
        events = store.get_contact_timeline(tenant_id=user.tenant_id, contact_id=contact_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return {
        "events": [
            {
                "id": event.id,
                "type": event.type,
                "source": event.source,
                "message": event.message,
                "form_id": event.form_id,
                "created_at": event.created_at,
            }
            for event in events
        ]
    }
