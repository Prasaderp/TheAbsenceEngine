import asyncio
import json
import uuid
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user, get_arq_pool
from app.schemas.analysis import AnalysisRequest, JobStatusResponse, JobListResponse
from app.schemas.report import ReportResponse, AbsenceItemResponse
from app.services import analysis_service, report_service
from app.shared import security
from app.shared.db import AsyncSessionLocal

router = APIRouter()


@router.post("", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_analysis(
    body: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
    arq=Depends(get_arq_pool),
):
    job = await analysis_service.submit_job(
        db, user_id, body.document_id, body.idempotency_key,
        body.domain_override, body.custom_schema_id, arq,
    )
    return JobStatusResponse.model_validate(job)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    jobs, meta = await analysis_service.list_jobs(db, user_id, page, per_page)
    return JobListResponse(
        data=[JobStatusResponse.model_validate(j) for j in jobs],
        meta=meta.model_dump(),
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    job = await analysis_service.get_job(db, user_id, job_id)
    return JobStatusResponse.model_validate(job)


@router.get("/{job_id}/report", response_model=ReportResponse)
async def get_job_report(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    report, items = await report_service.get_report_by_job(db, user_id, job_id)
    data = ReportResponse.model_validate(report)
    data.items = [AbsenceItemResponse.model_validate(i) for i in items]
    return data


@router.websocket("/{job_id}/stream")
async def stream_job(
    job_id: uuid.UUID,
    websocket: WebSocket,
    token: str,
):

    # Authenticate before accepting to avoid keeping rejected connections alive
    try:
        user_id = security.decode_access_token(token)
    except ValueError:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    terminal = {"completed", "failed"}
    try:
        async with AsyncSessionLocal() as db:
            while True:
                try:
                    job = await analysis_service.get_job(db, user_id, job_id)
                except Exception:
                    await websocket.send_text(
                        json.dumps({"status": "error", "error": "Job not found or access denied"})
                    )
                    break

                await websocket.send_text(
                    json.dumps({"status": job.status, "error": job.error_message})
                )

                if job.status in terminal:
                    break

                await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
