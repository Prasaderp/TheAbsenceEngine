import uuid
from sqlalchemy import UUID, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.db import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class AbsenceItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "absence_items"

    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    absence_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    evidence: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    suggested_completion: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (Index("ix_absence_items_report_risk", "report_id", "risk_score"),)
