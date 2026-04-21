from fastapi import APIRouter, Depends, HTTPException, Query, status

from .auth import get_current_user_and_tenant
from .contracts import error_responses
from .models import (
    ContentHistoryResponse,
    GenerateContentRequest,
    GenerateContentResponse,
    KeywordItem,
    KeywordSuggestRequest,
    KeywordSuggestResponse,
    SaveKeywordsRequest,
    SaveKeywordsResponse,
)
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/seo", tags=["seo-ai"])
UNSAFE_KEYWORD_TERMS = {"scam", "fraud", "phishing", "steal", "counterfeit"}


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


@router.post("/keywords/save", response_model=SaveKeywordsResponse, responses=error_responses(401, 422))
def save_keywords(
    payload: SaveKeywordsRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> SaveKeywordsResponse:
    user, _tenant = current
    return SaveKeywordsResponse(**store.save_keywords(tenant_id=user.tenant_id, workspace=payload.workspace, keywords=payload.keywords))


@router.post("/content/generate", response_model=GenerateContentResponse)
def generate_content(
    payload: GenerateContentRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> GenerateContentResponse:
    user, _tenant = current
    lowered = payload.keyword.lower()
    if any(term in lowered for term in UNSAFE_KEYWORD_TERMS):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsafe keyword policy violation")

    generated = store.generate_content(
        tenant_id=user.tenant_id,
        keyword=payload.keyword,
        content_type=payload.content_type,
        tone=payload.tone,
        language=payload.language,
        length=payload.length,
    )
    return GenerateContentResponse(**generated)


@router.get("/keywords/workspaces/{workspace}", response_model=SaveKeywordsResponse, responses=error_responses(401, 404))
def get_saved_keywords(
    workspace: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> SaveKeywordsResponse:
    user, _tenant = current
    return SaveKeywordsResponse(**store.get_saved_keywords(tenant_id=user.tenant_id, workspace=workspace))


@router.get("/content/history", response_model=ContentHistoryResponse, responses=error_responses(401))
def content_history(
    limit: int = Query(default=20, ge=1, le=100),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> ContentHistoryResponse:
    user, _tenant = current
    items = store.get_generated_content_history(tenant_id=user.tenant_id, limit=limit)
    return ContentHistoryResponse(total=len(items), items=items)
