import uuid
import pytest
from unittest.mock import AsyncMock


@pytest.fixture(autouse=True)
def mock_storage(monkeypatch):
    monkeypatch.setattr("app.services.document_service.storage.upload", AsyncMock(return_value="mock/key"))
    monkeypatch.setattr("app.services.document_service.storage.delete", AsyncMock())
    monkeypatch.setattr("app.services.document_service.storage.sha256", lambda data: "a" * 64)
    monkeypatch.setattr("app.services.document_service.storage.build_key", lambda *_: "mock/key")


async def _upload_doc(async_client, auth_headers) -> str:
    resp = await async_client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", b"Test document content for analysis.", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestAnalysisSubmit:
    @pytest.mark.asyncio
    async def test_submit_success(self, async_client, auth_headers):
        doc_id = await _upload_doc(async_client, auth_headers)
        resp = await async_client.post(
            "/api/v1/analysis",
            json={"document_id": doc_id, "idempotency_key": "submit-" + doc_id[:8]},
            headers=auth_headers,
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "pending"
        assert body["document_id"] == doc_id

    @pytest.mark.asyncio
    async def test_submit_idempotent(self, async_client, auth_headers):
        doc_id = await _upload_doc(async_client, auth_headers)
        key = "idem-" + doc_id[:8]
        r1 = await async_client.post(
            "/api/v1/analysis",
            json={"document_id": doc_id, "idempotency_key": key},
            headers=auth_headers,
        )
        r2 = await async_client.post(
            "/api/v1/analysis",
            json={"document_id": doc_id, "idempotency_key": key},
            headers=auth_headers,
        )
        assert r1.status_code == 202
        assert r2.status_code == 202
        assert r1.json()["id"] == r2.json()["id"]

    @pytest.mark.asyncio
    async def test_submit_nonexistent_document(self, async_client, auth_headers):
        resp = await async_client.post(
            "/api/v1/analysis",
            json={"document_id": str(uuid.uuid4()), "idempotency_key": "noexist-key-xyz1"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_submit_invalid_domain_override(self, async_client, auth_headers):
        doc_id = await _upload_doc(async_client, auth_headers)
        resp = await async_client.post(
            "/api/v1/analysis",
            json={
                "document_id": doc_id,
                "idempotency_key": "baddomain-" + doc_id[:6],
                "domain_override": "invalid_domain",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_requires_auth(self, async_client):
        resp = await async_client.post(
            "/api/v1/analysis",
            json={"document_id": str(uuid.uuid4()), "idempotency_key": "unauth-key-0001"},
        )
        assert resp.status_code in (401, 403)


class TestAnalysisGet:
    @pytest.mark.asyncio
    async def test_get_job_success(self, async_client, auth_headers):
        doc_id = await _upload_doc(async_client, auth_headers)
        create = await async_client.post(
            "/api/v1/analysis",
            json={"document_id": doc_id, "idempotency_key": "get-" + doc_id[:8]},
            headers=auth_headers,
        )
        job_id = create.json()["id"]
        resp = await async_client.get(f"/api/v1/analysis/{job_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, async_client, auth_headers):
        resp = await async_client.get(
            f"/api/v1/analysis/{uuid.uuid4()}", headers=auth_headers
        )
        assert resp.status_code == 404


class TestAnalysisList:
    @pytest.mark.asyncio
    async def test_list_jobs_paginated(self, async_client, auth_headers):
        doc_id = await _upload_doc(async_client, auth_headers)
        for i in range(3):
            await async_client.post(
                "/api/v1/analysis",
                json={
                    "document_id": doc_id,
                    "idempotency_key": f"listkey-{doc_id[:6]}-{i}",
                },
                headers=auth_headers,
            )
        resp = await async_client.get(
            "/api/v1/analysis?page=1&per_page=2", headers=auth_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) <= 2
        assert body["meta"]["per_page"] == 2
