from fastapi import APIRouter, Depends, Response, status

from .auth import get_current_user_and_tenant
from .models import ReportScheduleRequest
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


@router.get("/dashboard")
def dashboard(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> dict:
    user, _tenant = current
    kpis = store.analytics_dashboard(tenant_id=user.tenant_id)
    return {"kpis": kpis}


@router.get("/reports/export.csv")
def export_report(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> Response:
    user, _tenant = current
    csv_data = store.analytics_export_csv(tenant_id=user.tenant_id)
    return Response(content=csv_data, media_type="text/csv")


@router.post("/reports/schedule", status_code=status.HTTP_201_CREATED)
def schedule_report(
    payload: ReportScheduleRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> dict:
    user, _tenant = current
    scheduled = store.schedule_report(tenant_id=user.tenant_id, email=str(payload.email), frequency=payload.frequency)
    return {
        "id": scheduled["id"],
        "email": scheduled["email"],
        "frequency": scheduled["frequency"],
        "status": scheduled["status"],
    }
