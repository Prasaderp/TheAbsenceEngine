import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.shared.pagination import PageMeta


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    mime_type: str
    size_bytes: int
    domain: str | None
    domain_confidence: float | None
    checksum_sha256: str
    created_at: datetime


class DocumentListResponse(BaseModel):
    data: list[DocumentResponse]
    meta: PageMeta
