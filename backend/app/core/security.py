from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher

from .config import Settings

settings = Settings()
ph = PasswordHasher()


def verify_password_hash(plain: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, plain)
    except Exception:
        return False


def create_access_token(sub: str, minutes: int | None = None) -> str:
    exp_min = minutes or settings.token_expire_minutes
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=exp_min)).timestamp()),
        "nbf": int(now.timestamp()),
        "iss": "quietvector",
    }
    token = jwt.encode(payload, settings.get_jwt_secret(), algorithm="HS256")
    return token


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.get_jwt_secret(), algorithms=["HS256"], options={"require": ["exp", "sub"]})

