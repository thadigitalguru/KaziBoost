from uuid import uuid4

from fastapi import FastAPI, Request

from .ai_seo import router as ai_seo_router
from .analytics import router as analytics_router
from .auth import router as auth_router
from .crm import router as crm_router
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


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
