import uuid
from datetime import datetime
from sqlalchemy import UUID, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.db import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class AnalysisJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_jobs"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    domain_override: Mapped[str | None] = mapped_column(String(50), nullable=True)
    custom_schema_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_analysis_jobs_user_status", "user_id", "status"),)
