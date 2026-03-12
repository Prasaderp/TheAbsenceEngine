import asyncio
from collections.abc import Callable
from app.shared.logger import get_logger

log = get_logger(__name__)

_TASK_REGISTRY: dict[str, Callable] = {}


class InlineQueue:
    async def enqueue_job(self, fn_name: str, *args, **kwargs) -> None:
        fn = _TASK_REGISTRY.get(fn_name)
        if fn is None:
            raise RuntimeError(f"No inline task registered for '{fn_name}'")
        log.info("inline queue dispatching", extra={"task": fn_name})
        asyncio.create_task(fn({}, *args, **kwargs))

    async def aclose(self) -> None:
        pass
