from fastapi import FastAPI

from .ai_seo import router as ai_seo_router
from .auth import router as auth_router
from .crm import router as crm_router
from .sites import router as sites_router

app = FastAPI(title="KaziBoost API", version="0.1.0")
app.include_router(auth_router)
app.include_router(sites_router)
app.include_router(crm_router)
app.include_router(ai_seo_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
