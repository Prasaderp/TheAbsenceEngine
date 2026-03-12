import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from arq import create_pool
from arq.connections import RedisSettings
import redis.asyncio as aioredis
from .routes import api_router
from .config import settings
from .shared.errors import AppError, app_error_handler, unhandled_error_handler
from .shared.inline_queue import InlineQueue, _TASK_REGISTRY
from .shared.middleware import RequestContextMiddleware

logger = logging.getLogger(__name__)

_CORS_ORIGINS = [o.strip() for o in settings.cors_origins.split(",")]


def _register_inline_tasks() -> None:
    from worker.tasks import run_analysis
    _TASK_REGISTRY["run_analysis"] = run_analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Redis client for rate limiting (best-effort — not required)
    try:
        redis_client = await aioredis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        app.state.redis = redis_client
        logger.info("Redis connected for rate limiting.")
    except Exception as exc:
        app.state.redis = None
        logger.warning("Redis unavailable — rate limiting disabled. Error: %s", exc)

    # arq job queue
    try:
        base = RedisSettings.from_dsn(settings.redis_url)
        probe = RedisSettings(
            host=base.host,
            port=base.port,
            database=base.database,
            password=base.password,
            conn_timeout=2,
            conn_retries=0,
        )
        pool = await create_pool(probe)
        app.state.arq = pool
        logger.info("arq Redis pool connected.")
    except Exception as exc:
        if settings.app_env == "production":
            app.state.arq = None
            logger.warning(
                "Redis unavailable in production — job queue disabled. Error: %s", exc
            )
        else:
            _register_inline_tasks()
            app.state.arq = InlineQueue()
            logger.warning(
                "Redis unavailable — using in-process inline queue (dev only). Error: %s", exc
            )

    yield

    if app.state.arq is not None:
        await app.state.arq.aclose()
    if app.state.redis is not None:
        await app.state.redis.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="The Absence Engine",
        version="0.1.0",
        debug=False,
        lifespan=lifespan,
    )

    # Middleware order: outermost first (CORS handles preflight before anything else)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
    )
    app.add_middleware(RequestContextMiddleware)

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()

