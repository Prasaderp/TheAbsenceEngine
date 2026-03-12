import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SchemaCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    domain: str = Field(min_length=1, max_length=50)
    schema_definition: dict

    model_config = ConfigDict(extra="forbid")


class SchemaUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=100)
    schema_definition: dict | None = None

    model_config = ConfigDict(extra="forbid")


class SchemaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    domain: str
    schema_definition: dict
    created_at: datetime
    updated_at: datetime


class SchemaListResponse(BaseModel):
    data: list[SchemaResponse]
    meta: dict
