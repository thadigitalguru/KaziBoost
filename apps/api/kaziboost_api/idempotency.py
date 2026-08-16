from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Literal


ClaimResult = Literal["new", "replay", "conflict"]


class IdempotencyLedger:
    """Durable tenant/namespace/key ledger for safe retries and provider replays."""

    def __init__(self, db_path: str) -> None:
        resolved = Path(db_path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = resolved
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS idempotency_records (
                  tenant_id TEXT NOT NULL,
                  namespace TEXT NOT NULL,
                  idempotency_key TEXT NOT NULL,
                  payload_hash TEXT NOT NULL,
                  status TEXT NOT NULL DEFAULT 'claimed',
                  response_json TEXT,
                  created_at TEXT NOT NULL DEFAULT (datetime('now')),
                  PRIMARY KEY (tenant_id, namespace, idempotency_key)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_idempotency_created
                ON idempotency_records (created_at)
                """
            )

    def claim(
        self,
        tenant_id: str,
        namespace: str,
        idempotency_key: str,
        payload_hash: str,
    ) -> ClaimResult:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload_hash
                FROM idempotency_records
                WHERE tenant_id = ? AND namespace = ? AND idempotency_key = ?
                """,
                (tenant_id, namespace, idempotency_key),
            ).fetchone()
            if row:
                return "replay" if row["payload_hash"] == payload_hash else "conflict"
            connection.execute(
                """
                INSERT INTO idempotency_records
                  (tenant_id, namespace, idempotency_key, payload_hash)
                VALUES (?, ?, ?, ?)
                """,
                (tenant_id, namespace, idempotency_key, payload_hash),
            )
        return "new"

    def complete(
        self,
        tenant_id: str,
        namespace: str,
        idempotency_key: str,
        response: dict[str, object],
    ) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE idempotency_records
                SET status = 'completed', response_json = ?
                WHERE tenant_id = ? AND namespace = ? AND idempotency_key = ?
                """,
                (json.dumps(response, separators=(",", ":")), tenant_id, namespace, idempotency_key),
            )
        return cursor.rowcount == 1

    def response(self, tenant_id: str, namespace: str, idempotency_key: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT response_json
                FROM idempotency_records
                WHERE tenant_id = ? AND namespace = ? AND idempotency_key = ?
                """,
                (tenant_id, namespace, idempotency_key),
            ).fetchone()
        if not row or row["response_json"] is None:
            return None
        return json.loads(row["response_json"])
