"""create_report_and_items_tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-12 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "absence_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("overall_risk_score", sa.Float(), nullable=False),
        sa.Column("domain_detected", sa.String(50), nullable=False),
        sa.Column("metadata", JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_jobs.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
    )
    op.create_index(op.f("ix_absence_reports_job_id"), "absence_reports", ["job_id"], unique=True)
    op.create_index(op.f("ix_absence_reports_document_id"), "absence_reports", ["document_id"])
    op.create_index(op.f("ix_absence_reports_user_id"), "absence_reports", ["user_id"])
    op.create_index("ix_absence_reports_user_risk", "absence_reports", ["user_id", "overall_risk_score"])

    op.create_table(
        "absence_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("report_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("absence_type", sa.String(30), nullable=False),
        sa.Column("evidence", JSONB(), nullable=False, server_default="[]"),
        sa.Column("suggested_completion", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["absence_reports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_absence_items_report_id"), "absence_items", ["report_id"])
    op.create_index(op.f("ix_absence_items_category"), "absence_items", ["category"])
    op.create_index(op.f("ix_absence_items_absence_type"), "absence_items", ["absence_type"])
    op.create_index(op.f("ix_absence_items_risk_score"), "absence_items", ["risk_score"])
    op.create_index("ix_absence_items_report_risk", "absence_items", ["report_id", "risk_score"])


def downgrade() -> None:
    op.drop_index("ix_absence_items_report_risk", table_name="absence_items")
    op.drop_index(op.f("ix_absence_items_risk_score"), table_name="absence_items")
    op.drop_index(op.f("ix_absence_items_absence_type"), table_name="absence_items")
    op.drop_index(op.f("ix_absence_items_category"), table_name="absence_items")
    op.drop_index(op.f("ix_absence_items_report_id"), table_name="absence_items")
    op.drop_table("absence_items")

    op.drop_index("ix_absence_reports_user_risk", table_name="absence_reports")
    op.drop_index(op.f("ix_absence_reports_user_id"), table_name="absence_reports")
    op.drop_index(op.f("ix_absence_reports_document_id"), table_name="absence_reports")
    op.drop_index(op.f("ix_absence_reports_job_id"), table_name="absence_reports")
    op.drop_table("absence_reports")
