from __future__ import annotations

from typing import Protocol

from .seo_persistence import SEOPersistence


class GeneratedContentRepository(Protocol):
    """Tenant-scoped persistence contract for generated-content records."""

    def save(self, content: dict[str, object]) -> None: ...

    def get(self, tenant_id: str, record_id: str) -> dict[str, object] | None: ...

    def list(
        self,
        tenant_id: str,
        limit: int = 20,
        language: str | None = None,
    ) -> list[dict[str, object]]: ...

    def update_review(
        self,
        tenant_id: str,
        record_id: str,
        status: str,
        reviewed_by: str,
        reviewed_at: str,
        review_note: str | None,
    ) -> bool: ...


class SEOGeneratedContentRepository:
    """Adapter that keeps storage details out of domain services."""

    def __init__(self, persistence: SEOPersistence) -> None:
        self.persistence = persistence

    def save(self, content: dict[str, object]) -> None:
        self.persistence.save_generated_content(content)

    def get(self, tenant_id: str, record_id: str) -> dict[str, object] | None:
        return self.persistence.get_generated_content(tenant_id=tenant_id, content_id=record_id)

    def list(
        self,
        tenant_id: str,
        limit: int = 20,
        language: str | None = None,
    ) -> list[dict[str, object]]:
        return self.persistence.list_generated_content(
            tenant_id=tenant_id,
            limit=limit,
            language=language,
        )

    def update_review(
        self,
        tenant_id: str,
        record_id: str,
        status: str,
        reviewed_by: str,
        reviewed_at: str,
        review_note: str | None,
    ) -> bool:
        return self.persistence.update_generated_content_review(
            tenant_id=tenant_id,
            content_id=record_id,
            review_status=status,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
            review_note=review_note,
        )
