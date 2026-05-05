"""JWT authentication utilities."""

from __future__ import annotations

import base64
import hashlib
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt

from inndxd_core.config import settings


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600000)
    return f"pbkdf2_sha256${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        algo, salt_b64, dk_b64 = hashed_password.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
        actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, 600000)
        return actual == expected
    except (ValueError, base64.binascii.Error):
        return False


def create_access_token(user_id: UUID | str, tenant_id: str | None) -> str:
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes),
        "iat": datetime.now(UTC),
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
