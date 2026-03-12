import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.analysis_job import AnalysisJob
from app.models.document import Document
from app.shared.errors import NotFoundError, ConflictError, ValidationError
from app.shared.pagination import paginate, PageMeta
from app.shared.logger import get_logger

log = get_logger(__name__)

VALID_DOMAINS = {"legal", "product", "strategy", "technical", "interpersonal", "general"}


async def submit_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    idempotency_key: str,
    domain_override: str | None,
    custom_schema_id: uuid.UUID | None,
    arq_pool,
) -> AnalysisJob:
    existing = (
        await session.execute(
            select(AnalysisJob).where(AnalysisJob.idempotency_key == idempotency_key)
        )
    ).scalar_one_or_none()
    if existing:
        if existing.user_id != user_id:
            raise ValidationError("Idempotency key collision.")
        return existing

    doc = await session.get(Document, document_id)
    if not doc or doc.is_deleted or doc.user_id != user_id:
        raise NotFoundError("document")

    if domain_override and domain_override not in VALID_DOMAINS:
        raise ValidationError(f"Invalid domain: {domain_override}")

    job = AnalysisJob(
        document_id=document_id,
        user_id=user_id,
        status="pending",
        idempotency_key=idempotency_key,
        domain_override=domain_override,
        custom_schema_id=custom_schema_id,
    )
    session.add(job)
    await session.flush()

    await arq_pool.enqueue_job("run_analysis", str(job.id))
    log.info("Analysis job queued", extra={"job_id": str(job.id), "user_id": str(user_id)})
    return job


async def get_job(
    session: AsyncSession,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> AnalysisJob:
    job = await session.get(AnalysisJob, job_id)
    if not job or job.user_id != user_id:
        raise NotFoundError("job")
    return job


async def list_jobs(
    session: AsyncSession,
    user_id: uuid.UUID,
    page: int,
    per_page: int,
) -> tuple[list[AnalysisJob], PageMeta]:
    q = (
        select(AnalysisJob)
        .where(AnalysisJob.user_id == user_id)
        .order_by(AnalysisJob.created_at.desc())
    )
    rows, meta = await paginate(session, q, page, per_page)
    return list(rows), meta
