import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from arq import create_pool
from arq.connections import RedisSettings
from .routes import api_router
from .config import settings
from .shared.errors import AppError, app_error_handler, unhandled_error_handler
from .shared.inline_queue import InlineQueue, _TASK_REGISTRY

logger = logging.getLogger(__name__)

_CORS_ORIGINS = [o.strip() for o in getattr(settings, "cors_origins", "http://localhost:3000").split(",")]


def _register_inline_tasks() -> None:
    from worker.tasks import run_analysis
    _TASK_REGISTRY["run_analysis"] = run_analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
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


def create_app() -> FastAPI:
    app = FastAPI(
        title="The Absence Engine",
        version="0.1.0",
        debug=False,
        lifespan=lifespan,
    )

    # CORS — must be first middleware so preflight OPTIONS requests are handled
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
