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
                  created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )

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
                  title, meta_title, meta_description, body, related_terms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )

    def list_generated_content(self, tenant_id: str, limit: int = 20) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, keyword, content_type, tone, language, length, title,
                       meta_title, meta_description, body, related_terms, created_at
                FROM seo_generated_content
                WHERE tenant_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (tenant_id, limit),
            ).fetchall()

        return [
            {
                "id": row["id"],
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
                "created_at": row["created_at"],
            }
            for row in rows
        ]
