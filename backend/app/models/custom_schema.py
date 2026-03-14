import uuid
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.db import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin, UpdatedAtMixin


class CustomSchema(Base, UUIDPrimaryKeyMixin, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "custom_schemas"

    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    schema_definition: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
