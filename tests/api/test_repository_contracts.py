from pathlib import Path

from kaziboost_api.store import InMemoryStore


def test_generated_content_repository_is_tenant_scoped_and_supports_review_lifecycle(tmp_path: Path):
    store = InMemoryStore(db_path=str(tmp_path / "repositories.db"))
    repository = store.generated_content_repository

    content = store.generate_content(
        tenant_id="tenant-a",
        keyword="salon westlands",
        content_type="blog",
        tone="helpful",
        language="en",
        length="short",
    )

    assert repository.get(tenant_id="tenant-a", record_id=content["id"])["tenant_id"] == "tenant-a"
    assert repository.get(tenant_id="tenant-b", record_id=content["id"]) is None
    assert repository.list(tenant_id="tenant-b") == []

    assert repository.update_review(
        tenant_id="tenant-a",
        record_id=content["id"],
        status="approved",
        reviewed_by="user-a",
        reviewed_at="2026-08-16T00:00:00+00:00",
        review_note="Looks good",
    ) is True
    assert repository.get(tenant_id="tenant-a", record_id=content["id"])["status"] == "approved"
