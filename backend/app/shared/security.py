import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
import argon2
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
from app.config import settings

_ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def _encode(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _decode(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def create_access_token(user_id: uuid.UUID) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return _encode({"sub": str(user_id), "type": "access", "exp": exp})


def create_refresh_token(user_id: uuid.UUID) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    return _encode({"sub": str(user_id), "type": "refresh", "exp": exp})


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = _decode(token)
        if payload.get("type") != "access":
            raise ValueError("invalid token type")
        return uuid.UUID(payload["sub"])
    except Exception as e:
        raise ValueError("invalid or expired token") from e


def decode_refresh_token(token: str) -> uuid.UUID:
    try:
        payload = _decode(token)
        if payload.get("type") != "refresh":
            raise ValueError("invalid token type")
        return uuid.UUID(payload["sub"])
    except Exception as e:
        raise ValueError("invalid or expired token") from e
