import uuid
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.schemas.report import ReportResponse, ReportListResponse, AbsenceItemResponse
from app.services import report_service

router = APIRouter()


@router.get("", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    reports, meta = await report_service.list_reports(db, user_id, page, per_page)
    return ReportListResponse(
        data=[ReportResponse.model_validate(r) for r in reports],
        meta=meta,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    report, items = await report_service.get_report(db, user_id, report_id)
    data = ReportResponse.model_validate(report)
    data.items = [AbsenceItemResponse.model_validate(i) for i in items]
    return data


@router.get("/{report_id}/export")
async def export_report(
    report_id: uuid.UUID,
    format: str = Query("json", pattern="^(json|pdf)$"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    if format == "pdf":
        data = await report_service.export_pdf(db, user_id, report_id)
        return Response(content=data, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.pdf"'})
    data = await report_service.export_json(db, user_id, report_id)
    return Response(content=data, media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="report-{report_id}.json"'})


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    await report_service.delete_report(db, user_id, report_id)
