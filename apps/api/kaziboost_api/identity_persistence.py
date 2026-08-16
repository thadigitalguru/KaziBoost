from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class IdentityPersistence:
    """Durable identity adapter used by the identity repository contract.

    The adapter is intentionally storage-focused. Authentication policy, hashing,
    authorization, and token expiry remain in the application/domain layer.
    """

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
                CREATE TABLE IF NOT EXISTS identity_tenants (
                  id TEXT PRIMARY KEY,
                  name TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS identity_users (
                  id TEXT PRIMARY KEY,
                  tenant_id TEXT NOT NULL REFERENCES identity_tenants(id),
                  owner_name TEXT NOT NULL,
                  email TEXT NOT NULL UNIQUE,
                  role TEXT NOT NULL,
                  password_hash TEXT NOT NULL,
                  password_salt TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_identity_users_tenant ON identity_users (tenant_id)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS identity_sessions (
                  token TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL REFERENCES identity_users(id),
                  expires_at TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS identity_mfa (
                  user_id TEXT PRIMARY KEY REFERENCES identity_users(id),
                  secret TEXT NOT NULL,
                  backup_codes TEXT NOT NULL,
                  enabled INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS identity_mfa_challenges (
                  id TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL REFERENCES identity_users(id),
                  code TEXT NOT NULL,
                  status TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_identity_challenges_user ON identity_mfa_challenges (user_id)"
            )

    def save_tenant(self, tenant_id: str, name: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO identity_tenants (id, name) VALUES (?, ?)",
                (tenant_id, name),
            )

    def save_user(
        self,
        user_id: str,
        tenant_id: str,
        owner_name: str,
        email: str,
        role: str,
        password_hash: str,
        password_salt: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO identity_users
                  (id, tenant_id, owner_name, email, role, password_hash, password_salt)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, tenant_id, owner_name, email, role, password_hash, password_salt),
            )

    def get_user_by_email(self, email: str, tenant_id: str | None = None) -> dict[str, object] | None:
        query = "SELECT id, tenant_id, owner_name, email, role, password_hash, password_salt FROM identity_users WHERE email = ?"
        params: tuple[object, ...] = (email,)
        if tenant_id is not None:
            query += " AND tenant_id = ?"
            params += (tenant_id,)
        with self._connect() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_user(self, user_id: str, tenant_id: str | None = None) -> dict[str, object] | None:
        query = "SELECT id, tenant_id, owner_name, email, role, password_hash, password_salt FROM identity_users WHERE id = ?"
        params: tuple[object, ...] = (user_id,)
        if tenant_id is not None:
            query += " AND tenant_id = ?"
            params += (tenant_id,)
        with self._connect() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def save_session(self, token: str, user_id: str, expires_at: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO identity_sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
                (token, user_id, expires_at),
            )

    def get_session(self, token: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT token, user_id, expires_at FROM identity_sessions WHERE token = ?",
                (token,),
            ).fetchone()
        return dict(row) if row else None

    def revoke_session(self, token: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM identity_sessions WHERE token = ?", (token,))

    def save_mfa(self, user_id: str, secret: str, backup_codes: list[str], enabled: bool = True) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO identity_mfa (user_id, secret, backup_codes, enabled)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, secret, json.dumps(backup_codes), int(enabled)),
            )

    def get_mfa(self, user_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT user_id, secret, backup_codes, enabled FROM identity_mfa WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["backup_codes"] = json.loads(result["backup_codes"])
        result["enabled"] = bool(result["enabled"])
        return result

    def save_challenge(self, challenge_id: str, user_id: str, code: str, status: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO identity_mfa_challenges (id, user_id, code, status)
                VALUES (?, ?, ?, ?)
                """,
                (challenge_id, user_id, code, status),
            )

    def get_challenge(self, challenge_id: str, user_id: str | None = None) -> dict[str, object] | None:
        query = "SELECT id, user_id, code, status, created_at FROM identity_mfa_challenges WHERE id = ?"
        params: tuple[object, ...] = (challenge_id,)
        if user_id is not None:
            query += " AND user_id = ?"
            params += (user_id,)
        with self._connect() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def update_challenge_status(self, challenge_id: str, user_id: str, status: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE identity_mfa_challenges SET status = ? WHERE id = ? AND user_id = ?",
                (status, challenge_id, user_id),
            )
        return cursor.rowcount == 1
