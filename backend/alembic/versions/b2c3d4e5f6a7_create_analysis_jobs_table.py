"""create_analysis_jobs_table

Revision ID: b2c3d4e5f6a7
Revises: 73fcb2fcb877
Create Date: 2026-03-12 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "73fcb2fcb877"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("domain_override", sa.String(length=50), nullable=True),
        sa.Column("custom_schema_id", sa.UUID(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(op.f("ix_analysis_jobs_document_id"), "analysis_jobs", ["document_id"])
    op.create_index(op.f("ix_analysis_jobs_user_id"), "analysis_jobs", ["user_id"])
    op.create_index(op.f("ix_analysis_jobs_status"), "analysis_jobs", ["status"])
    op.create_index("ix_analysis_jobs_user_status", "analysis_jobs", ["user_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_analysis_jobs_user_status", table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_status"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_user_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_document_id"), table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
