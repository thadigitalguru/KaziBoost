from fastapi import APIRouter, Depends, Query

from .auth import get_current_user_and_tenant
from .models import (
    GenerateContentRequest,
    GenerateContentResponse,
    KeywordItem,
    KeywordSuggestRequest,
    KeywordSuggestResponse,
    SaveKeywordsRequest,
)
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/seo", tags=["seo-ai"])


@router.post("/keywords/suggest", response_model=KeywordSuggestResponse)
def suggest_keywords(
    payload: KeywordSuggestRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> KeywordSuggestResponse:
    _user, _tenant = current
    items = store.suggest_keywords(
        seed_query=payload.seed_query,
        location=payload.location,
        language=payload.language,
    )
    keyword_items = [KeywordItem(**item) for item in items]
    return KeywordSuggestResponse(total=len(keyword_items), items=keyword_items)


@router.post("/keywords/save")
def save_keywords(
    payload: SaveKeywordsRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> dict:
    user, _tenant = current
    return store.save_keywords(tenant_id=user.tenant_id, workspace=payload.workspace, keywords=payload.keywords)


@router.post("/content/generate", response_model=GenerateContentResponse)
def generate_content(
    payload: GenerateContentRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> GenerateContentResponse:
    _user, _tenant = current
    user, _tenant = current
    generated = store.generate_content(
        tenant_id=user.tenant_id,
        keyword=payload.keyword,
        content_type=payload.content_type,
        tone=payload.tone,
        language=payload.language,
        length=payload.length,
    )
    return GenerateContentResponse(**generated)


@router.get("/keywords/workspaces/{workspace}")
def get_saved_keywords(
    workspace: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> dict:
    user, _tenant = current
    return store.get_saved_keywords(tenant_id=user.tenant_id, workspace=workspace)


@router.get("/content/history")
def content_history(
    limit: int = Query(default=20, ge=1, le=100),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> dict:
    user, _tenant = current
    items = store.get_generated_content_history(tenant_id=user.tenant_id, limit=limit)
    return {"total": len(items), "items": items}
