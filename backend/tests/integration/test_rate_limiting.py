import pytest
from unittest.mock import AsyncMock, patch
from app.shared.errors import AppError


def _rl_side_effect(*_, **__):
    raise AppError("RATE_LIMIT_EXCEEDED", "Too many requests.", 429)


class TestRateLimitingIntegration:
    @pytest.mark.asyncio
    async def test_auth_rate_limit_enforced(self, async_client):
        """When RateLimiter.check raises AppError(429), login returns 429."""
        with patch(
            "app.shared.rate_limiter.RateLimiter.check",
            new=AsyncMock(side_effect=_rl_side_effect),
        ):
            resp = await async_client.post(
                "/api/v1/auth/login",
                json={"email": "rl@test.com", "password": "password123"},
            )
        assert resp.status_code == 429
        assert resp.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_upload_rate_limit_enforced(self, async_client, auth_headers):
        """Rate limit on upload returns 429 when limiter fires."""
        with patch(
            "app.shared.rate_limiter.RateLimiter.check",
            new=AsyncMock(side_effect=_rl_side_effect),
        ):
            resp = await async_client.post(
                "/api/v1/documents",
                files={"file": ("test.txt", b"content", "text/plain")},
                headers=auth_headers,
            )
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_analysis_rate_limit_enforced(self, async_client, auth_headers):
        """Rate limit on analysis submit returns 429 when limiter fires."""
        import uuid
        with patch(
            "app.shared.rate_limiter.RateLimiter.check",
            new=AsyncMock(side_effect=_rl_side_effect),
        ):
            resp = await async_client.post(
                "/api/v1/analysis",
                json={"document_id": str(uuid.uuid4()), "idempotency_key": "rl-test-01"},
                headers=auth_headers,
            )
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_no_rate_limit_when_redis_unavailable(self, async_client):
        """When RateLimiter has redis=None, check() is a no-op and requests pass freely."""
        with patch(
            "app.dependencies.getattr",
            return_value=None,
        ):
            resp = await async_client.post(
                "/api/v1/auth/register",
                json={"email": "nolimit@test.com", "password": "password123", "name": "NoLimit"},
            )
        assert resp.status_code in (201, 409)

    @pytest.mark.asyncio
    async def test_response_has_request_id_header(self, async_client):
        """Middleware must inject X-Request-ID on every response."""
        resp = await async_client.get("/api/v1/health")
        assert "x-request-id" in resp.headers

    @pytest.mark.asyncio
    async def test_response_has_security_headers(self, async_client):
        """Security headers must be present on every response."""
        resp = await async_client.get("/api/v1/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
