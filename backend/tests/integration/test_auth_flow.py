import pytest


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, async_client):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "new@test.com", "password": "password123", "name": "New User"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_conflicts(self, async_client):
        payload = {"email": "dup@test.com", "password": "password123", "name": "Dup"}
        await async_client.post("/api/v1/auth/register", json=payload)
        resp = await async_client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_short_password_rejected(self, async_client):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "short@test.com", "password": "abc", "name": "Short"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email_rejected(self, async_client):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "validpassword", "name": "Bad"},
        )
        assert resp.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, async_client):
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "login@test.com", "password": "loginpass1", "name": "Login"},
        )
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "login@test.com", "password": "loginpass1"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, async_client):
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "wrongpw@test.com", "password": "correctpass1", "name": "WrongPW"},
        )
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpw@test.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_email(self, async_client):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@test.com", "password": "anything123"},
        )
        assert resp.status_code == 401


class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_valid_token(self, async_client):
        reg = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "refresh@test.com", "password": "refreshpass1", "name": "Refresh"},
        )
        refresh_token = reg.json()["refresh_token"]
        resp = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, async_client):
        resp = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "garbage.token.here"},
        )
        assert resp.status_code == 401


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_returns_204(self, async_client):
        resp = await async_client.post("/api/v1/auth/logout")
        assert resp.status_code == 204
