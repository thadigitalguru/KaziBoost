from fastapi import APIRouter, Depends, Query, status

from .auth import get_current_user_and_tenant
from .models import TrainingArticleCreateRequest, TrainingArticleListResponse, TrainingArticleOut
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
    return TrainingArticleOut(id=article.id, title=article.title, content=article.content, category=article.category)


@router.get("/articles/search", response_model=TrainingArticleListResponse)
def search_articles(
    q: str = Query(min_length=2),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> TrainingArticleListResponse:
    user, _tenant = current
    items = store.search_training_articles(tenant_id=user.tenant_id, query=q)
    results = [TrainingArticleOut(id=item.id, title=item.title, content=item.content, category=item.category) for item in items]
    return TrainingArticleListResponse(total=len(results), items=results)
