from fastapi import APIRouter, Depends, HTTPException, Query, status

from .auth import get_current_user_and_tenant
from .models import (
    TrainingArticleCreateRequest,
    TrainingArticleListResponse,
    TrainingArticleOut,
    TrainingArticleUpdateRequest,
    TrainingCategoryListResponse,
)
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/training", tags=["training"])


@router.post("/articles", response_model=TrainingArticleOut, status_code=status.HTTP_201_CREATED)
def create_article(
    payload: TrainingArticleCreateRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> TrainingArticleOut:
    user, _tenant = current
    article = store.create_training_article(
        tenant_id=user.tenant_id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
    )
    return TrainingArticleOut(
        id=article.id,
        title=article.title,
        content=article.content,
        category=article.category,
        featured=article.featured,
    )


@router.get("/articles", response_model=TrainingArticleListResponse)
def list_articles(
    featured: bool | None = Query(default=None),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> TrainingArticleListResponse:
    user, _tenant = current
    items = store.list_training_articles(tenant_id=user.tenant_id, featured=featured)
    results = [
        TrainingArticleOut(
            id=item.id,
            title=item.title,
            content=item.content,
            category=item.category,
            featured=item.featured,
        )
        for item in items
    ]
    return TrainingArticleListResponse(total=len(results), items=results)


@router.get("/articles/search", response_model=TrainingArticleListResponse)
def search_articles(
    q: str = Query(min_length=2),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> TrainingArticleListResponse:
    user, _tenant = current
    items = store.search_training_articles(tenant_id=user.tenant_id, query=q)
    results = [
        TrainingArticleOut(
            id=item.id,
            title=item.title,
            content=item.content,
            category=item.category,
            featured=item.featured,
        )
        for item in items
    ]
    return TrainingArticleListResponse(total=len(results), items=results)


@router.patch("/articles/{article_id}", response_model=TrainingArticleOut)
def update_article(
    article_id: str,
    payload: TrainingArticleUpdateRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> TrainingArticleOut:
    user, _tenant = current
    try:
        item = store.update_training_article(
            tenant_id=user.tenant_id,
            article_id=article_id,
            title=payload.title,
            content=payload.content,
            category=payload.category,
            featured=payload.featured,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TrainingArticleOut(
        id=item.id,
        title=item.title,
        content=item.content,
        category=item.category,
        featured=item.featured,
    )


@router.get("/categories", response_model=TrainingCategoryListResponse)
def categories(
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> TrainingCategoryListResponse:
    user, _tenant = current
    items = store.list_training_categories(tenant_id=user.tenant_id)
    return TrainingCategoryListResponse(total=len(items), items=items)


@router.delete("/articles/{article_id}")
def delete_article(
    article_id: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> dict:
    user, _tenant = current
    try:
        store.delete_training_article(tenant_id=user.tenant_id, article_id=article_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"id": article_id, "status": "deleted"}
