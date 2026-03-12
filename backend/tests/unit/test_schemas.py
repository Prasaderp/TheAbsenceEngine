import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services import schema_service
from app.shared.errors import NotFoundError


def _make_schema(user_id=None, **kwargs):
    s = MagicMock()
    s.id = uuid.uuid4()
    s.user_id = user_id or uuid.uuid4()
    s.name = kwargs.get("name", "Test Schema")
    s.domain = kwargs.get("domain", "legal")
    s.schema_definition = kwargs.get("schema_definition", {"required_sections": ["scope_of_work"]})
    return s


@pytest.mark.asyncio
class TestGetSchema:
    async def test_not_found_raises(self):
        session = AsyncMock()
        session.get.return_value = None
        with pytest.raises(NotFoundError):
            await schema_service.get_schema(session, uuid.uuid4(), uuid.uuid4())

    async def test_wrong_user_raises(self):
        session = AsyncMock()
        s = _make_schema(user_id=uuid.uuid4())
        session.get.return_value = s
        with pytest.raises(NotFoundError):
            await schema_service.get_schema(session, uuid.uuid4(), s.id)

    async def test_correct_user_returns(self):
        session = AsyncMock()
        uid = uuid.uuid4()
        s = _make_schema(user_id=uid)
        session.get.return_value = s
        result = await schema_service.get_schema(session, uid, s.id)
        assert result is s


@pytest.mark.asyncio
class TestCreateSchema:
    async def test_creates_and_flushes(self):
        session = AsyncMock()
        uid = uuid.uuid4()
        result = await schema_service.create_schema(
            session, uid, "My NDA", "legal", {"required_sections": ["termination_clause"]}
        )
        session.add.assert_called_once()
        session.flush.assert_called_once()
        assert result.user_id == uid
        assert result.name == "My NDA"
        assert result.domain == "legal"


@pytest.mark.asyncio
class TestDeleteSchema:
    async def test_deletes(self):
        session = AsyncMock()
        uid = uuid.uuid4()
        s = _make_schema(user_id=uid)
        session.get.return_value = s
        await schema_service.delete_schema(session, uid, s.id)
        session.delete.assert_called_once_with(s)
