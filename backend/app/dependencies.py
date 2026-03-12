import uuid
from typing import AsyncGenerator
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.db import AsyncSessionLocal
from app.shared.errors import AppError
from app.shared import security
from app.shared.rate_limiter import RateLimiter, _parse_rate, get_client_ip
from app.config import settings

_bearer = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> uuid.UUID:
    try:
        return security.decode_access_token(creds.credentials)
    except ValueError:
        raise AppError("UNAUTHORIZED", "Invalid or expired token.", 401)


def get_arq_pool(request: Request):
    pool = request.app.state.arq
    if pool is None:
        raise AppError("SERVICE_UNAVAILABLE", "Job queue is not available. Redis is not connected.", 503)
    return pool


def _make_limiter(spec: str):
    """Return a FastAPI dependency that enforces *spec* per IP."""
    limit, window = _parse_rate(spec)

    async def _enforce(request: Request) -> None:
        redis = getattr(request.app.state, "redis", None)
        limiter = RateLimiter(redis, limit, window)
        ip = get_client_ip(request)
        await limiter.check(ip)

    return _enforce


rate_limit_auth = _make_limiter(settings.rate_limit_auth)
rate_limit_upload = _make_limiter(settings.rate_limit_upload)
rate_limit_analysis = _make_limiter(settings.rate_limit_analysis)
