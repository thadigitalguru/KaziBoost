from pathlib import Path
import sqlite3

from kaziboost_api.store import InMemoryStore


def test_saved_keywords_persist_across_store_instances(tmp_path: Path):
    db_path = tmp_path / "kaziboost-test.db"

    store_a = InMemoryStore(db_path=str(db_path))
    result = store_a.save_keywords(
        tenant_id="tenant-1",
        workspace="salon-seo",
        keywords=["best salon westlands", "salon near me westlands"],
    )

    assert result["count"] == 2

    store_b = InMemoryStore(db_path=str(db_path))
    restored = store_b.get_saved_keywords(tenant_id="tenant-1", workspace="salon-seo")

    assert restored["workspace"] == "salon-seo"
    assert restored["count"] == 2
    assert "best salon westlands" in restored["keywords"]


def test_generated_content_history_is_persisted_by_tenant(tmp_path: Path):
    db_path = tmp_path / "kaziboost-test.db"

    store_a = InMemoryStore(db_path=str(db_path))
    generated = store_a.generate_content(
        tenant_id="tenant-2",
        keyword="vet clinic nairobi",
        content_type="blog",
        tone="conversational",
        language="en",
        length="medium",
    )

    assert generated["title"]

    store_b = InMemoryStore(db_path=str(db_path))
    history = store_b.get_generated_content_history(tenant_id="tenant-2")

    assert len(history) >= 1
    assert history[0]["keyword"] == "vet clinic nairobi"
    assert history[0]["language"] == "en"


def test_generated_content_query_indexes_and_readiness_are_available(tmp_path: Path):
    db_path = tmp_path / "kaziboost-ready.db"

    store = InMemoryStore(db_path=str(db_path))

    assert store.storage_ready() is True
    with sqlite3.connect(db_path) as conn:
        indexes = {row[1] for row in conn.execute("PRAGMA index_list('seo_generated_content')")}

    assert "idx_seo_generated_content_tenant_created" in indexes
    assert "idx_seo_generated_content_tenant_language_created" in indexes


def test_storage_readiness_fails_when_expected_index_is_missing(tmp_path: Path):
    db_path = tmp_path / "kaziboost-ready-fails.db"

    store = InMemoryStore(db_path=str(db_path))
    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP INDEX idx_seo_generated_content_tenant_language_created")

    assert store.storage_ready() is False
