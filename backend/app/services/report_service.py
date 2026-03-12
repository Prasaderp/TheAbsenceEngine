import io
import json
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.absence_report import AbsenceReport
from app.models.absence_item import AbsenceItem
from app.shared.errors import NotFoundError
from app.shared.pagination import paginate, PageMeta
from app.shared.logger import get_logger

log = get_logger(__name__)


async def _get_report(session: AsyncSession, user_id: uuid.UUID, report_id: uuid.UUID) -> AbsenceReport:
    report = await session.get(AbsenceReport, report_id)
    if not report or report.is_deleted or report.user_id != user_id:
        raise NotFoundError("report")
    return report


async def _items(session: AsyncSession, report_id: uuid.UUID) -> list[AbsenceItem]:
    rows = await session.execute(
        select(AbsenceItem)
        .where(AbsenceItem.report_id == report_id)
        .order_by(AbsenceItem.sort_order)
    )
    return list(rows.scalars())


async def list_reports(
    session: AsyncSession,
    user_id: uuid.UUID,
    page: int,
    per_page: int,
) -> tuple[list[AbsenceReport], PageMeta]:
    q = (
        select(AbsenceReport)
        .where(AbsenceReport.user_id == user_id, AbsenceReport.is_deleted.is_(False))
        .order_by(AbsenceReport.created_at.desc())
    )
    rows, meta = await paginate(session, q, page, per_page)
    return list(rows), meta


async def get_report(
    session: AsyncSession,
    user_id: uuid.UUID,
    report_id: uuid.UUID,
) -> tuple[AbsenceReport, list[AbsenceItem]]:
    report = await _get_report(session, user_id, report_id)
    items = await _items(session, report.id)
    return report, items


async def get_report_by_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> tuple[AbsenceReport, list[AbsenceItem]]:
    result = await session.execute(
        select(AbsenceReport).where(
            AbsenceReport.job_id == job_id,
            AbsenceReport.user_id == user_id,
            AbsenceReport.is_deleted.is_(False),
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundError("report")
    items = await _items(session, report.id)
    return report, items


async def delete_report(
    session: AsyncSession,
    user_id: uuid.UUID,
    report_id: uuid.UUID,
) -> None:
    report = await _get_report(session, user_id, report_id)
    report.is_deleted = True
    log.info("Report deleted", extra={"user_id": str(user_id), "report_id": str(report_id)})


async def export_json(
    session: AsyncSession,
    user_id: uuid.UUID,
    report_id: uuid.UUID,
) -> bytes:
    report, items = await get_report(session, user_id, report_id)
    payload = {
        "id": str(report.id),
        "job_id": str(report.job_id),
        "document_id": str(report.document_id),
        "summary": report.summary,
        "overall_risk_score": report.overall_risk_score,
        "domain_detected": report.domain_detected,
        "metadata": report.metadata_,
        "created_at": report.created_at.isoformat(),
        "items": [
            {
                "id": str(i.id),
                "title": i.title,
                "category": i.category,
                "absence_type": i.absence_type,
                "description": i.description,
                "reasoning": i.reasoning,
                "confidence": i.confidence,
                "risk_score": i.risk_score,
                "evidence": i.evidence,
                "suggested_completion": i.suggested_completion,
            }
            for i in items
        ],
    }
    return json.dumps(payload, indent=2).encode()


async def export_pdf(
    session: AsyncSession,
    user_id: uuid.UUID,
    report_id: uuid.UUID,
) -> bytes:
    report, items = await get_report(session, user_id, report_id)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        from reportlab.lib.units import cm
    except ImportError as e:
        raise RuntimeError("reportlab not installed") from e

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Absence Report — {report.domain_detected.upper()}", styles["Title"]),
        Spacer(1, 0.4 * cm),
        Paragraph(report.summary, styles["Normal"]),
        Spacer(1, 0.3 * cm),
        Paragraph(f"<b>Overall Risk Score:</b> {report.overall_risk_score:.2f}", styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]
    for item in items:
        story += [
            Paragraph(f"[{item.risk_score:.2f}] {item.title}", styles["Heading2"]),
            Paragraph(item.description, styles["Normal"]),
            Paragraph(f"<i>Reasoning:</i> {item.reasoning}", styles["Normal"]),
            Spacer(1, 0.3 * cm),
        ]
    doc.build(story)
    return buf.getvalue()
