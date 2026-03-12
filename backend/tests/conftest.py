import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from app.main import app
from app.dependencies import get_db, get_arq_pool
from app.shared.db import Base

TEST_DB_URL = "postgresql+asyncpg://postgres:test1234@localhost:5432/absence_engine"

_engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
_TestSession = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)


class _FakeArq:
    async def enqueue_job(self, *args, **kwargs):
        pass


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    import asyncio
    async def _run():
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.get_event_loop().run_until_complete(_run())
    yield
    async def _teardown():
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    asyncio.get_event_loop().run_until_complete(_teardown())


@pytest_asyncio.fixture
async def db_session():
    async with _TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client(db_session):
    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_arq_pool] = lambda: _FakeArq()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(async_client):
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "testpass123", "name": "Test User"},
    )
    if resp.status_code == 409:
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpass123"},
        )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
