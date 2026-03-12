import pytest
from unittest.mock import AsyncMock, MagicMock
from app.shared.rate_limiter import RateLimiter, _parse_rate, get_client_ip
from app.shared.errors import AppError
from app.shared.middleware import _SECURITY_HEADERS


class TestParseRate:
    def test_per_minute(self):
        count, window = _parse_rate("5/minute")
        assert count == 5
        assert window == 60

    def test_per_second(self):
        count, window = _parse_rate("100/second")
        assert count == 100
        assert window == 1

    def test_per_hour(self):
        count, window = _parse_rate("1000/hour")
        assert count == 1000
        assert window == 3600


class TestGetClientIp:
    def test_forwarded_header(self):
        req = MagicMock()
        req.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
        assert get_client_ip(req) == "1.2.3.4"

    def test_direct_client(self):
        req = MagicMock()
        req.headers = {}
        req.client.host = "9.10.11.12"
        assert get_client_ip(req) == "9.10.11.12"

    def test_no_client(self):
        req = MagicMock()
        req.headers = {}
        req.client = None
        assert get_client_ip(req) == "unknown"


@pytest.mark.asyncio
class TestRateLimiter:
    def _make_redis(self, count: int):
        redis = MagicMock()
        pipe = MagicMock()
        pipe.zremrangebyscore = MagicMock()
        pipe.zadd = MagicMock()
        pipe.zcard = MagicMock()
        pipe.expire = MagicMock()
        pipe.execute = AsyncMock(return_value=[None, None, count, None])
        redis.pipeline.return_value = pipe
        return redis

    async def test_allows_within_limit(self):
        limiter = RateLimiter(self._make_redis(3), limit=5, window_seconds=60)
        await limiter.check("key")

    async def test_raises_when_exceeded(self):
        limiter = RateLimiter(self._make_redis(6), limit=5, window_seconds=60)
        with pytest.raises(AppError) as exc:
            await limiter.check("key")
        assert exc.value.status == 429
        assert exc.value.code == "RATE_LIMIT_EXCEEDED"

    async def test_skips_when_redis_none(self):
        limiter = RateLimiter(None, limit=0, window_seconds=1)
        await limiter.check("key")

    async def test_skips_on_redis_error(self):
        redis = MagicMock()
        pipe = MagicMock()
        pipe.execute = AsyncMock(side_effect=ConnectionError("redis down"))
        redis.pipeline.return_value = pipe
        limiter = RateLimiter(redis, limit=5, window_seconds=60)
        await limiter.check("key")


class TestSecurityHeaders:
    def test_all_required_headers_present(self):
        assert "X-Content-Type-Options" in _SECURITY_HEADERS
        assert "X-Frame-Options" in _SECURITY_HEADERS
        assert "X-XSS-Protection" in _SECURITY_HEADERS
        assert "Referrer-Policy" in _SECURITY_HEADERS
        assert "Cache-Control" in _SECURITY_HEADERS

    def test_header_values(self):
        assert _SECURITY_HEADERS["X-Frame-Options"] == "DENY"
        assert _SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"
