import uuid
from typing import AsyncGenerator
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.db import AsyncSessionLocal
from app.shared.errors import AppError
from app.shared import security

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
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "Job queue is not available. Redis is not connected.",
            503,
        )
    return pool
