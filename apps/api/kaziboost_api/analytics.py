from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from .auth import get_current_user_and_tenant
from .contracts import error_responses
from .models import (
    AnalyticsConnectorListResponse,
    AnalyticsConnectorRequest,
    AnalyticsConnectorResponse,
    AnalyticsConnectorUpdateRequest,
    AnalyticsDashboardResponse,
    AnalyticsDashboardSummaryResponse,
    ReportScheduleUpdateRequest,
    AnalyticsFunnelResponse,
    ReportScheduleListResponse,
    ReportScheduleRequest,
    ReportScheduleResponse,
)
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboardResponse, responses=error_responses(401))
def dashboard(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> AnalyticsDashboardResponse:
    user, _tenant = current
    kpis = store.analytics_dashboard(tenant_id=user.tenant_id)
    return AnalyticsDashboardResponse(kpis=kpis)


@router.get("/dashboard/summary", response_model=AnalyticsDashboardSummaryResponse)
def dashboard_summary(
    days: int = 7,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> AnalyticsDashboardSummaryResponse:
    user, _tenant = current
    if days < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="days must be at least 1")
    days = min(days, 90)
    return AnalyticsDashboardSummaryResponse(**store.analytics_dashboard_summary(tenant_id=user.tenant_id, days=days))


@router.get("/funnel", response_model=AnalyticsFunnelResponse, responses=error_responses(401))
def funnel(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> AnalyticsFunnelResponse:
    user, _tenant = current
    payload = store.analytics_funnel(tenant_id=user.tenant_id)
    return AnalyticsFunnelResponse(**payload)


@router.get("/dashboard/trend")
def dashboard_trend(
    days: int = 7,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> dict:
    user, _tenant = current
    if days < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="days must be at least 1")
    days = min(days, 90)
    return store.analytics_trend_snapshot(tenant_id=user.tenant_id, days=days)


@router.post("/connectors", status_code=status.HTTP_201_CREATED, response_model=AnalyticsConnectorResponse)
def create_connector(
    payload: AnalyticsConnectorRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> AnalyticsConnectorResponse:
    user, _tenant = current
    return AnalyticsConnectorResponse(**store.create_analytics_connector(
        tenant_id=user.tenant_id,
        provider=payload.provider,
        property_id=payload.property_id,
        status=payload.status,
    ))


@router.get("/connectors", response_model=AnalyticsConnectorListResponse)
def list_connectors(
    provider: str | None = Query(default=None),
    status: str | None = Query(default=None),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> AnalyticsConnectorListResponse:
    user, _tenant = current
    items = [
        AnalyticsConnectorResponse(**item)
        for item in store.list_analytics_connectors(tenant_id=user.tenant_id, provider=provider, status=status)
    ]
    return AnalyticsConnectorListResponse(total=len(items), items=items)


@router.patch("/connectors/{connector_id}", response_model=AnalyticsConnectorResponse)
def update_connector(
    connector_id: str,
    payload: AnalyticsConnectorUpdateRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> AnalyticsConnectorResponse:
    user, _tenant = current
    try:
        item = store.update_analytics_connector(tenant_id=user.tenant_id, connector_id=connector_id, status=payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AnalyticsConnectorResponse(**item)


@router.delete("/connectors/{connector_id}")
def delete_connector(
    connector_id: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> dict:
    user, _tenant = current
    try:
        item = store.delete_analytics_connector(tenant_id=user.tenant_id, connector_id=connector_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"status": "deleted", "id": item["id"]}


@router.get("/reports/export.pdf")
def export_report_pdf(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> Response:
    user, _tenant = current
    pdf_data = store.analytics_export_pdf(tenant_id=user.tenant_id)
    return Response(content=pdf_data, media_type="application/pdf")


@router.get("/reports/export.csv")
def export_report(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> Response:
    user, _tenant = current
    csv_data = store.analytics_export_csv(tenant_id=user.tenant_id)
    return Response(content=csv_data, media_type="text/csv")


@router.post(
    "/reports/schedule",
    status_code=status.HTTP_201_CREATED,
    response_model=ReportScheduleResponse,
    responses=error_responses(401, 422),
)
def schedule_report(
    payload: ReportScheduleRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> ReportScheduleResponse:
    user, _tenant = current
    scheduled = store.schedule_report(tenant_id=user.tenant_id, email=str(payload.email), frequency=payload.frequency)
    return ReportScheduleResponse(
        id=scheduled["id"],
        email=scheduled["email"],
        frequency=scheduled["frequency"],
        status=scheduled["status"],
    )


@router.get("/reports/schedules", response_model=ReportScheduleListResponse)
def list_schedules(
    status: str | None = Query(default=None),
    frequency: str | None = Query(default=None),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> ReportScheduleListResponse:
    user, _tenant = current
    items = [
        ReportScheduleResponse(**item)
        for item in store.list_report_schedules(tenant_id=user.tenant_id, status=status, frequency=frequency)
    ]
    return ReportScheduleListResponse(total=len(items), items=items)


@router.patch("/reports/schedules/{schedule_id}", response_model=ReportScheduleResponse, responses=error_responses(404))
def update_schedule(
    schedule_id: str,
    payload: ReportScheduleUpdateRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> ReportScheduleResponse:
    user, _tenant = current
    try:
        item = store.update_report_schedule(tenant_id=user.tenant_id, schedule_id=schedule_id, frequency=payload.frequency)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ReportScheduleResponse(**item)


@router.delete("/reports/schedules/{schedule_id}", response_model=ReportScheduleResponse, responses=error_responses(404))
def cancel_schedule(
    schedule_id: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> ReportScheduleResponse:
    user, _tenant = current
    try:
        item = store.cancel_report_schedule(tenant_id=user.tenant_id, schedule_id=schedule_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ReportScheduleResponse(**item)
