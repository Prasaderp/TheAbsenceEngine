import time
from fastapi import Request
from app.shared.errors import AppError
from app.shared.logger import get_logger

log = get_logger(__name__)


def _parse_rate(spec: str) -> tuple[int, int]:
    """Parse '10/minute' → (10, 60). Supports second|minute|hour."""
    count, unit = spec.split("/")
    windows = {"second": 1, "minute": 60, "hour": 3600}
    return int(count), windows[unit.strip().lower()]


class RateLimiter:
    """Sliding-window rate limiter backed by Redis.

    Falls back silently when Redis is unavailable (dev/offline).
    Each call increments a z-set keyed by identifier and prunes old entries.
    """

    def __init__(self, redis_client, limit: int, window_seconds: int) -> None:
        self._redis = redis_client
        self._limit = limit
        self._window = window_seconds

    async def check(self, key: str) -> None:
        """Raise 429 AppError if key has exceeded the rate limit."""
        if self._redis is None:
            return
        now = time.time()
        window_start = now - self._window
        rkey = f"rl:{key}"
        try:
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(rkey, "-inf", window_start)
            pipe.zadd(rkey, {str(now): now})
            pipe.zcard(rkey)
            pipe.expire(rkey, self._window)
            results = await pipe.execute()
            count = results[2]
            if count > self._limit:
                log.warning(
                    "rate limit exceeded",
                    extra={"key": key, "count": count, "limit": self._limit},
                )
                raise AppError(
                    "RATE_LIMIT_EXCEEDED",
                    f"Too many requests. Limit: {self._limit} per {self._window}s.",
                    429,
                )
        except AppError:
            raise
        except Exception as exc:
            log.warning("rate limiter redis error; skipping", extra={"error": str(exc)})


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
