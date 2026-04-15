import hashlib
import os
import secrets


def _pbkdf2(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 390000).hex()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = _pbkdf2(password, salt)
    return f"{salt.hex()}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_hex, digest = password_hash.split("$", 1)
        computed = _pbkdf2(password, bytes.fromhex(salt_hex))
        return secrets.compare_digest(computed, digest)
    except ValueError:
        return False
