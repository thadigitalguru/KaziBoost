from __future__ import annotations

import hashlib
import hmac
import secrets


ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str, legacy_salt: str | None = None) -> bool:
    if encoded.startswith(f"{ALGORITHM}$"):
        try:
            algorithm, iterations_text, salt_hex, expected_hex = encoded.split("$", 3)
            if algorithm != ALGORITHM:
                return False
            iterations = int(iterations_text)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(expected_hex)
        except (ValueError, TypeError):
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)

    if legacy_salt is None:
        return False
    legacy_digest = hashlib.sha256(f"{legacy_salt}:{password}".encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy_digest, encoded)


def needs_rehash(encoded: str) -> bool:
    if not encoded.startswith(f"{ALGORITHM}$"):
        return True
    try:
        _algorithm, iterations_text, _salt_hex, _digest_hex = encoded.split("$", 3)
        return int(iterations_text) != ITERATIONS
    except (ValueError, TypeError):
        return True
