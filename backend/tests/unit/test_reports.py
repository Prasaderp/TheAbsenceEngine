import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services import report_service
from app.shared.errors import NotFoundError


def _make_report(**kwargs):
    r = MagicMock()
    r.id = kwargs.get("id", uuid.uuid4())
    r.job_id = kwargs.get("job_id", uuid.uuid4())
    r.document_id = kwargs.get("document_id", uuid.uuid4())
    r.user_id = kwargs.get("user_id", uuid.uuid4())
    r.summary = kwargs.get("summary", "Test summary")
    r.overall_risk_score = kwargs.get("overall_risk_score", 0.5)
    r.domain_detected = kwargs.get("domain_detected", "legal")
    r.metadata_ = kwargs.get("metadata_", {})
    r.is_deleted = kwargs.get("is_deleted", False)
    r.created_at = datetime.now(timezone.utc)
    return r


def _make_item(**kwargs):
    i = MagicMock()
    i.id = uuid.uuid4()
    i.report_id = kwargs.get("report_id", uuid.uuid4())
    i.title = "Missing Force Majeure"
    i.category = "legal_protection"
    i.absence_type = "coverage_gap"
    i.description = "No force majeure clause found."
    i.reasoning = "Standard contracts include this."
    i.confidence = 0.9
    i.risk_score = 0.8
    i.evidence = []
    i.suggested_completion = None
    i.sort_order = 0
    return i


@pytest.mark.asyncio
class TestGetReport:
    async def test_not_found_raises(self):
        session = AsyncMock()
        session.get.return_value = None
        uid = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await report_service._get_report(session, uid, uuid.uuid4())

    async def test_wrong_user_raises(self):
        session = AsyncMock()
        report = _make_report(user_id=uuid.uuid4())
        session.get.return_value = report
        with pytest.raises(NotFoundError):
            await report_service._get_report(session, uuid.uuid4(), report.id)

    async def test_deleted_raises(self):
        session = AsyncMock()
        uid = uuid.uuid4()
        report = _make_report(user_id=uid, is_deleted=True)
        session.get.return_value = report
        with pytest.raises(NotFoundError):
            await report_service._get_report(session, uid, report.id)

    async def test_valid_returns_report(self):
        session = AsyncMock()
        uid = uuid.uuid4()
        report = _make_report(user_id=uid)
        session.get.return_value = report
        result = await report_service._get_report(session, uid, report.id)
        assert result is report


@pytest.mark.asyncio
class TestDeleteReport:
    async def test_soft_delete(self):
        session = AsyncMock()
        uid = uuid.uuid4()
        report = _make_report(user_id=uid)
        session.get.return_value = report
        await report_service.delete_report(session, uid, report.id)
        assert report.is_deleted is True


@pytest.mark.asyncio
class TestExportJson:
    async def test_json_structure(self):
        session = AsyncMock()
        uid = uuid.uuid4()
        report = _make_report(user_id=uid)
        item = _make_item(report_id=report.id)

        session.get.return_value = report

        result_mock = MagicMock()
        result_mock.scalars.return_value = [item]
        session.execute.return_value = result_mock

        raw = await report_service.export_json(session, uid, report.id)
        data = json.loads(raw)
        assert data["summary"] == "Test summary"
        assert data["overall_risk_score"] == 0.5
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Missing Force Majeure"


@pytest.mark.asyncio
class TestExportPdf:
    async def test_pdf_returns_bytes(self):
        pytest.importorskip("reportlab")
        session = AsyncMock()
        uid = uuid.uuid4()
        report = _make_report(user_id=uid)
        item = _make_item(report_id=report.id)

        session.get.return_value = report

        result_mock = MagicMock()
        result_mock.scalars.return_value = [item]
        session.execute.return_value = result_mock

        raw = await report_service.export_pdf(session, uid, report.id)
        assert raw[:4] == b"%PDF"

    async def test_pdf_missing_reportlab_raises(self):
        import builtins
        import sys
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name.startswith("reportlab"):
                raise ImportError("no module")
            return real_import(name, *args, **kwargs)

        session = AsyncMock()
        uid = uuid.uuid4()
        report = _make_report(user_id=uid)
        item = _make_item(report_id=report.id)
        session.get.return_value = report
        result_mock = MagicMock()
        result_mock.scalars.return_value = [item]
        session.execute.return_value = result_mock

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(RuntimeError, match="reportlab not installed"):
                await report_service.export_pdf(session, uid, report.id)
