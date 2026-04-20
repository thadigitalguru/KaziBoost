from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from .ai_seo import router as ai_seo_router
from .analytics import router as analytics_router
from .auth import router as auth_router
from .crm import router as crm_router
from .errors import http_exception_handler, validation_exception_handler
from .models import HealthResponse, ReadinessResponse
from .payments import router as payments_router
from .sites import router as sites_router
from .whatsapp import router as whatsapp_router

app = FastAPI(title="KaziBoost API", version="0.1.0")
app.include_router(auth_router)
app.include_router(sites_router)
app.include_router(crm_router)
app.include_router(ai_seo_router)
app.include_router(whatsapp_router)
app.include_router(payments_router)
app.include_router(analytics_router)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["x-frame-options"] = "DENY"
    response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
    response.headers["content-security-policy"] = "default-src 'self'"
    if request.url.path.startswith("/v1/auth"):
        response.headers["cache-control"] = "no-store"
        response.headers["pragma"] = "no-cache"
    return response


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/ready", response_model=ReadinessResponse)
def ready() -> ReadinessResponse:
    return ReadinessResponse(status="ready", checks={"api": "ok", "storage": "ok"})
