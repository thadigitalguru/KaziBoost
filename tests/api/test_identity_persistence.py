from pathlib import Path

from kaziboost_api.identity_persistence import IdentityPersistence


def test_identity_records_and_sessions_survive_restart(tmp_path: Path):
    db_path = tmp_path / "identity.db"
    first = IdentityPersistence(str(db_path))

    first.save_tenant("tenant-a", "A Shop")
    first.save_user(
        user_id="user-a",
        tenant_id="tenant-a",
        owner_name="Owner",
        email="owner@example.com",
        role="owner",
        password_hash="encoded-hash",
        password_salt="",
    )
    first.save_session("session-a", "user-a", "2099-01-01T00:00:00+00:00")

    second = IdentityPersistence(str(db_path))

    user = second.get_user_by_email("owner@example.com")
    assert user is not None
    assert user["tenant_id"] == "tenant-a"
    assert second.get_user_by_email("owner@example.com", tenant_id="tenant-b") is None
    assert second.get_session("session-a")["user_id"] == "user-a"

    second.revoke_session("session-a")
    assert second.get_session("session-a") is None


def test_mfa_and_challenges_are_tenant_user_scoped(tmp_path: Path):
    persistence = IdentityPersistence(str(tmp_path / "identity.db"))
    persistence.save_tenant("tenant-a", "A Shop")
    persistence.save_user("user-a", "tenant-a", "Owner", "owner@example.com", "owner", "hash", "")
    persistence.save_mfa("user-a", "secret", ["backup-a"])
    persistence.save_challenge("challenge-a", "user-a", "code-a", "pending")

    assert persistence.get_mfa("user-a")["secret"] == "secret"
    assert persistence.get_challenge("challenge-a")["user_id"] == "user-a"
    assert persistence.get_challenge("challenge-a", user_id="other-user") is None
