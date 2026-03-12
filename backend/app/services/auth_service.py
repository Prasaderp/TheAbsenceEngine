import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.shared.errors import ConflictError, AppError
from app.shared import security
from app.shared.logger import get_logger

log = get_logger(__name__)


async def register(session: AsyncSession, email: str, password: str, name: str) -> tuple[User, str, str]:
    existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        raise ConflictError("Email already registered.")

    user = User(email=email, password_hash=security.hash_password(password), name=name)
    session.add(user)
    await session.flush()

    access = security.create_access_token(user.id)
    refresh = security.create_refresh_token(user.id)
    log.info("User registered", extra={"user_id": str(user.id)})
    return user, access, refresh


async def login(session: AsyncSession, email: str, password: str) -> tuple[User, str, str]:
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if not user or not security.verify_password(password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "Invalid email or password.", 401)

    access = security.create_access_token(user.id)
    refresh = security.create_refresh_token(user.id)
    log.info("User login", extra={"user_id": str(user.id)})
    return user, access, refresh


def refresh_tokens(refresh_token: str) -> tuple[str, str]:
    try:
        user_id = security.decode_refresh_token(refresh_token)
    except ValueError:
        raise AppError("INVALID_TOKEN", "Invalid or expired refresh token.", 401)

    access = security.create_access_token(user_id)
    new_refresh = security.create_refresh_token(user_id)
    return access, new_refresh
