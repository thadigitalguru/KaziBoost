import hashlib

from kaziboost_api.passwords import hash_password, needs_rehash, verify_password


def test_passwords_use_versioned_slow_hashes():
    encoded = hash_password("StrongPass123!")

    assert encoded.startswith("pbkdf2_sha256$")
    assert verify_password("StrongPass123!", encoded) is True
    assert verify_password("WrongPass123!", encoded) is False
    assert needs_rehash(encoded) is False


def test_legacy_sha256_hashes_verify_and_require_rehash():
    salt = "legacy-salt"
    legacy_hash = hashlib.sha256(f"{salt}:StrongPass123!".encode("utf-8")).hexdigest()

    assert verify_password("StrongPass123!", legacy_hash, legacy_salt=salt) is True
    assert needs_rehash(legacy_hash) is True
