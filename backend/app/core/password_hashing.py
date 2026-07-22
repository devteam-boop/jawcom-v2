"""Argon2id password hashing + password policy.

Argon2id (via argon2-cffi) is used in preference to bcrypt per this task's
spec. ``PasswordHasher`` defaults (time_cost=3, memory_cost=64MB,
parallelism=4) are already tuned for Argon2id per the library's own
guidance — not overridden here.
"""

import re
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

_hasher = PasswordHasher()

_MIN_LENGTH = 6
_SPECIAL_CHARS = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`]")


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, password_hash: Optional[str]) -> bool:
    """False (never raises) for a missing hash, wrong password, or a hash
    in a format Argon2 can't parse — a bad/legacy hash must fail closed."""
    if not password_hash:
        return False
    try:
        return _hasher.verify(password_hash, plain)
    except (VerifyMismatchError, InvalidHashError, ValueError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """True if the hash was made with older/weaker params than the
    current PasswordHasher config — caller should re-hash on next login."""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


def validate_password_policy(plain: str) -> Optional[str]:
    """Returns an error message, or None if the password satisfies policy:
    6+ chars, upper, lower, number, special character."""
    if len(plain) < _MIN_LENGTH:
        return f"Password must be at least {_MIN_LENGTH} characters"
    if not re.search(r"[A-Z]", plain):
        return "Password must contain an uppercase letter"
    if not re.search(r"[a-z]", plain):
        return "Password must contain a lowercase letter"
    if not re.search(r"[0-9]", plain):
        return "Password must contain a number"
    if not _SPECIAL_CHARS.search(plain):
        return "Password must contain a special character"
    return None
