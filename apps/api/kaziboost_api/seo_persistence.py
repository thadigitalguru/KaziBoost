from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class SEOPersistence:
    def __init__(self, db_path: str | None = None) -> None:
        resolved = Path(db_path or "data/kaziboost.db")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = resolved
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_generated_content_columns(self, conn: sqlite3.Connection) -> None:
        columns = {row[1] for row in conn.execute("PRAGMA table_info('seo_generated_content')")}
        additions = {
            "prompt_version": "TEXT NOT NULL DEFAULT 'seo-deterministic-v1'",
            "generation_mode": "TEXT NOT NULL DEFAULT 'deterministic_template'",
            "safety_outcome": "TEXT NOT NULL DEFAULT 'safe'",
            "policy_violations": "TEXT NOT NULL DEFAULT '[]'",
            "status": "TEXT NOT NULL DEFAULT 'needs_review'",
            "reviewed_by": "TEXT",
            "reviewed_at": "TEXT",
            "review_note": "TEXT",
        }
        for column, definition in additions.items():
            if column not in columns:
                try:
                    conn.execute(f"ALTER TABLE seo_generated_content ADD COLUMN {column} {definition}")
                except sqlite3.OperationalError as exc:
                    if "duplicate column name" not in str(exc).lower():
                        raise

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seo_saved_keywords (
                  tenant_id TEXT NOT NULL,
                  workspace TEXT NOT NULL,
                  keyword TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT (datetime('now')),
                  PRIMARY KEY (tenant_id, workspace, keyword)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seo_generated_content (
                  id TEXT PRIMARY KEY,
                  tenant_id TEXT NOT NULL,
                  keyword TEXT NOT NULL,
                  content_type TEXT NOT NULL,
                  tone TEXT NOT NULL,
                  language TEXT NOT NULL,
                  length TEXT NOT NULL,
                  title TEXT NOT NULL,
                  meta_title TEXT NOT NULL,
                  meta_description TEXT NOT NULL,
                  body TEXT NOT NULL,
                  related_terms TEXT NOT NULL,
                  prompt_version TEXT NOT NULL DEFAULT 'seo-deterministic-v1',
                  generation_mode TEXT NOT NULL DEFAULT 'deterministic_template',
                  safety_outcome TEXT NOT NULL DEFAULT 'safe',
                  policy_violations TEXT NOT NULL DEFAULT '[]',
                  status TEXT NOT NULL DEFAULT 'needs_review',
                  reviewed_by TEXT,
                  reviewed_at TEXT,
                  review_note TEXT,
                  created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            self._ensure_generated_content_columns(conn)
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_seo_generated_content_tenant_created
                ON seo_generated_content (tenant_id, created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_seo_generated_content_tenant_language_created
                ON seo_generated_content (tenant_id, language, created_at DESC)
                """
            )

    def check_ready(self) -> bool:
        try:
            with self._connect() as conn:
                conn.execute("SELECT 1 FROM seo_generated_content LIMIT 1").fetchone()
        except sqlite3.Error:
            return False
        return True

    def save_keywords(self, tenant_id: str, workspace: str, keywords: list[str]) -> list[str]:
        normalized = sorted({keyword.strip() for keyword in keywords if keyword.strip()})
        with self._connect() as conn:
            for keyword in normalized:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO seo_saved_keywords (tenant_id, workspace, keyword)
                    VALUES (?, ?, ?)
                    """,
                    (tenant_id, workspace, keyword),
                )

        return self.get_keywords(tenant_id=tenant_id, workspace=workspace)

    def get_keywords(self, tenant_id: str, workspace: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT keyword
                FROM seo_saved_keywords
                WHERE tenant_id = ? AND workspace = ?
                ORDER BY keyword ASC
                """,
                (tenant_id, workspace),
            ).fetchall()
        return [row["keyword"] for row in rows]

    def save_generated_content(self, content: dict[str, object]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO seo_generated_content (
                  id, tenant_id, keyword, content_type, tone, language, length,
                  title, meta_title, meta_description, body, related_terms,
                  prompt_version, generation_mode, safety_outcome, policy_violations,
                  status, reviewed_by, reviewed_at, review_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content["id"],
                    content["tenant_id"],
                    content["keyword"],
                    content["content_type"],
                    content["tone"],
                    content["language"],
                    content["length"],
                    content["title"],
                    content["meta_title"],
                    content["meta_description"],
                    content["body"],
                    json.dumps(content["related_terms"]),
                    content["prompt_version"],
                    content["generation_mode"],
                    content["safety_outcome"],
                    json.dumps(content["policy_violations"]),
                    content.get("status", "needs_review"),
                    content.get("reviewed_by"),
                    content.get("reviewed_at"),
                    content.get("review_note"),
                ),
            )

    def update_generated_content_review(
        self,
        tenant_id: str,
        content_id: str,
        review_status: str,
        reviewed_by: str,
        reviewed_at: str,
        review_note: str | None,
    ) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE seo_generated_content
                SET status = ?, reviewed_by = ?, reviewed_at = ?, review_note = ?
                WHERE tenant_id = ? AND id = ?
                """,
                (review_status, reviewed_by, reviewed_at, review_note, tenant_id, content_id),
            )
        return cursor.rowcount == 1

    def get_generated_content(self, tenant_id: str, content_id: str) -> dict[str, object] | None:
        items = self.list_generated_content(tenant_id=tenant_id, limit=1, content_id=content_id)
        return items[0] if items else None

    def list_generated_content(
        self,
        tenant_id: str,
        limit: int = 20,
        language: str | None = None,
        content_id: str | None = None,
    ) -> list[dict[str, object]]:
        with self._connect() as conn:
            if language:
                rows = conn.execute(
                    """
                    SELECT id, tenant_id, keyword, content_type, tone, language, length, title,
                           meta_title, meta_description, body, related_terms,
                           prompt_version, generation_mode, safety_outcome, policy_violations,
                           status, reviewed_by, reviewed_at, review_note, created_at
                    FROM seo_generated_content
                    WHERE tenant_id = ? AND language = ?
                      AND (? IS NULL OR id = ?)
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (tenant_id, language, content_id, content_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, tenant_id, keyword, content_type, tone, language, length, title,
                           meta_title, meta_description, body, related_terms,
                           prompt_version, generation_mode, safety_outcome, policy_violations,
                           status, reviewed_by, reviewed_at, review_note, created_at
                    FROM seo_generated_content
                    WHERE tenant_id = ?
                      AND (? IS NULL OR id = ?)
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (tenant_id, content_id, content_id, limit),
                ).fetchall()

        return [
            {
                "id": row["id"],
                "tenant_id": row["tenant_id"],
                "keyword": row["keyword"],
                "content_type": row["content_type"],
                "tone": row["tone"],
                "language": row["language"],
                "length": row["length"],
                "title": row["title"],
                "meta_title": row["meta_title"],
                "meta_description": row["meta_description"],
                "body": row["body"],
                "related_terms": json.loads(row["related_terms"]),
                "prompt_version": row["prompt_version"],
                "generation_mode": row["generation_mode"],
                "safety_outcome": row["safety_outcome"],
                "policy_violations": json.loads(row["policy_violations"]),
                "status": row["status"],
                "reviewed_by": row["reviewed_by"],
                "reviewed_at": row["reviewed_at"],
                "review_note": row["review_note"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
