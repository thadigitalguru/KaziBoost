from pathlib import Path

from kaziboost_api.idempotency import IdempotencyLedger


def test_idempotency_ledger_distinguishes_new_replay_and_conflict(tmp_path: Path):
    ledger = IdempotencyLedger(str(tmp_path / "idempotency.db"))

    first = ledger.claim("tenant-a", "mpesa-callback", "provider-event-1", "hash-a")
    replay = ledger.claim("tenant-a", "mpesa-callback", "provider-event-1", "hash-a")
    conflict = ledger.claim("tenant-a", "mpesa-callback", "provider-event-1", "hash-b")

    assert first == "new"
    assert replay == "replay"
    assert conflict == "conflict"

    ledger.complete(
        "tenant-a",
        "mpesa-callback",
        "provider-event-1",
        {"payment_id": "payment-1", "status": "success"},
    )
    assert ledger.response("tenant-a", "mpesa-callback", "provider-event-1") == {
        "payment_id": "payment-1",
        "status": "success",
    }


def test_idempotency_keys_are_tenant_and_namespace_scoped(tmp_path: Path):
    ledger = IdempotencyLedger(str(tmp_path / "idempotency.db"))

    assert ledger.claim("tenant-a", "whatsapp", "event-1", "hash") == "new"
    assert ledger.claim("tenant-b", "whatsapp", "event-1", "hash") == "new"
    assert ledger.claim("tenant-a", "payments", "event-1", "hash") == "new"
