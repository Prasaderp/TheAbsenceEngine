import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


VALID_STATUSES = {"pending", "processing", "completed", "failed"}
VALID_DOMAINS = {"legal", "product", "strategy", "technical", "interpersonal", "general"}


class AnalysisRequest(BaseModel):
    document_id: uuid.UUID
    idempotency_key: str = Field(min_length=8, max_length=64)
    domain_override: str | None = Field(None)
    custom_schema_id: uuid.UUID | None = None

    model_config = ConfigDict(extra="forbid")


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    domain_override: str | None
    error_message: str | None
    created_at: datetime


class JobListResponse(BaseModel):
    data: list[JobStatusResponse]
    meta: dict
