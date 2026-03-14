import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from app.config import settings
from app.models.analysis_job import AnalysisJob
from app.models.document import Document
from app.models.absence_report import AbsenceReport
from app.models.absence_item import AbsenceItem
from app.shared import storage as _storage
from app.shared.logger import get_logger
from app.engine.orchestrator import run_pipeline

log = get_logger(__name__)

_engine = create_async_engine(settings.database_url, poolclass=NullPool)
_Session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine, class_=AsyncSession, expire_on_commit=False
)


async def run_analysis(ctx: dict, job_id: str) -> None:
    jid = uuid.UUID(job_id)
    async with _Session() as session:
        job = await session.get(AnalysisJob, jid)
        if not job:
            log.error("job not found", extra={"job_id": job_id})
            return

        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        await session.commit()
        log.info("analysis started", extra={"job_id": job_id})

        try:
            doc = await session.get(Document, job.document_id)
            if not doc:
                raise ValueError("document record missing")

            file_data = await _storage.get_bytes(doc.storage_key)
            report_data = await run_pipeline(file_data, doc.mime_type, job.domain_override)

            report = AbsenceReport(
                job_id=jid,
                document_id=doc.id,
                user_id=job.user_id,
                summary=report_data["summary"],
                overall_risk_score=report_data["overall_risk_score"],
                domain_detected=report_data["domain_detected"],
                metadata_={"domain_confidence": report_data.get("domain_confidence", 0.0)},
            )
            session.add(report)
            await session.flush()

            for idx, item in enumerate(report_data.get("items", [])):
                session.add(
                    AbsenceItem(
                        report_id=report.id,
                        category=item["category"],
                        title=item["title"],
                        description=item["description"],
                        reasoning=item["reasoning"],
                        confidence=item["confidence"],
                        risk_score=item["risk_score"],
                        absence_type=item["absence_type"],
                        evidence=item.get("evidence", []),
                        suggested_completion=item.get("suggested_completion"),
                        sort_order=idx,
                    )
                )

            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            log.info("analysis completed", extra={"job_id": job_id, "items": len(report_data.get("items", []))})

        except Exception as exc:
            job.status = "failed"
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = str(exc)[:500]
            log.error("analysis failed", extra={"job_id": job_id, "error": str(exc)})
        finally:
            await session.commit()
