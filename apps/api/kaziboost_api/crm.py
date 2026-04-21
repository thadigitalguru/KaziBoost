from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from .auth import get_current_user_and_tenant
from .models import (
    CRMFormCreateRequest,
    CRMFormOut,
    CampaignHistoryItem,
    CampaignHistoryResponse,
    CampaignSendRequest,
    CampaignSendResponse,
    ContactConsentUpdateRequest,
    ContactExportResponse,
    ContactListResponse,
    ContactOut,
    ContactTimelineEvent,
    ContactTimelineResponse,
    LeadSubmissionOut,
    LeadSubmitRequest,
    SegmentCreateRequest,
    SegmentOut,
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
        consent=contact.consent,
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


@router.post("/segments", response_model=SegmentOut, status_code=status.HTTP_201_CREATED)
def create_segment(
    payload: SegmentCreateRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> SegmentOut:
    user, _ = current
    segment = store.create_segment(
        tenant_id=user.tenant_id,
        name=payload.name,
        tag=payload.tag,
        source=payload.source,
    )
    return SegmentOut(id=segment.id, name=segment.name, tag=segment.tag, source=segment.source)


@router.get("/segments/{segment_id}/contacts", response_model=ContactListResponse)
def segment_contacts(segment_id: str, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> ContactListResponse:
    user, _ = current
    try:
        items = store.get_segment_contacts(tenant_id=user.tenant_id, segment_id=segment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    contacts = [_contact_out(contact) for contact in items]
    return ContactListResponse(total=len(contacts), items=contacts)


@router.post("/campaigns/send", response_model=CampaignSendResponse, status_code=status.HTTP_201_CREATED)
def send_campaign(
    payload: CampaignSendRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> CampaignSendResponse:
    user, _ = current
    campaign = store.send_campaign(
        tenant_id=user.tenant_id,
        channel=payload.channel,
        subject=payload.subject,
        message=payload.message,
        tag=payload.tag,
        source=payload.source,
    )
    return CampaignSendResponse(
        id=campaign.id,
        channel=campaign.channel,
        subject=campaign.subject,
        recipients=campaign.recipients,
    )


@router.get("/campaigns/history", response_model=CampaignHistoryResponse)
def campaign_history(current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> CampaignHistoryResponse:
    user, _ = current
    items = [
        CampaignHistoryItem(
            id=item.id,
            channel=item.channel,
            subject=item.subject,
            recipients=item.recipients,
            created_at=item.created_at,
        )
        for item in store.campaign_history(tenant_id=user.tenant_id)
    ]
    return CampaignHistoryResponse(total=len(items), items=items)


@router.patch("/contacts/{contact_id}/consent")
def update_consent(
    contact_id: str,
    payload: ContactConsentUpdateRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> dict:
    user, _ = current
    try:
        contact = store.update_contact_consent(
            tenant_id=user.tenant_id,
            contact_id=contact_id,
            email_marketing=payload.email_marketing,
            sms_marketing=payload.sms_marketing,
            actor_user_id=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return {"contact_id": contact.id, "consent": contact.consent}


@router.get("/contacts/{contact_id}/export", response_model=ContactExportResponse)
def export_contact(contact_id: str, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> ContactExportResponse:
    user, _ = current
    try:
        contact = store.get_contact(tenant_id=user.tenant_id, contact_id=contact_id)
        events = store.get_contact_timeline(tenant_id=user.tenant_id, contact_id=contact_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ContactExportResponse(
        contact=_contact_out(contact),
        timeline=[
            ContactTimelineEvent(
                id=event.id,
                type=event.type,
                source=event.source,
                message=event.message,
                form_id=event.form_id,
                created_at=event.created_at,
            )
            for event in events
        ],
    )


@router.delete("/contacts/{contact_id}")
def anonymize_contact(contact_id: str, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> dict:
    user, _ = current
    try:
        store.anonymize_contact(tenant_id=user.tenant_id, contact_id=contact_id, actor_user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"contact_id": contact_id, "status": "anonymized"}


@router.get("/contacts/{contact_id}/timeline", response_model=ContactTimelineResponse)
def contact_timeline(contact_id: str, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> ContactTimelineResponse:
    user, _ = current
    try:
        events = store.get_contact_timeline(tenant_id=user.tenant_id, contact_id=contact_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ContactTimelineResponse(
        events=[
            ContactTimelineEvent(
                id=event.id,
                type=event.type,
                source=event.source,
                message=event.message,
                form_id=event.form_id,
                created_at=event.created_at,
            )
            for event in events
        ]
    )
