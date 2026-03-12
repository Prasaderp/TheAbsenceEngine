import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AbsenceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    title: str
    description: str
    reasoning: str
    confidence: float
    risk_score: float
    absence_type: str
    evidence: list
    suggested_completion: str | None
    sort_order: int


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    document_id: uuid.UUID
    summary: str
    overall_risk_score: float
    domain_detected: str
    metadata_: dict
    created_at: datetime
    items: list[AbsenceItemResponse] = []


class ReportListResponse(BaseModel):
    data: list[ReportResponse]
    meta: dict
