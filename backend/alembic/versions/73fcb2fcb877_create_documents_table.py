"""create_documents_table

Revision ID: 73fcb2fcb877
Revises: a1b2c3d4e5f6
Create Date: 2026-03-12 09:21:15.466073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73fcb2fcb877'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('documents',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=False),
    sa.Column('storage_key', sa.String(length=500), nullable=False),
    sa.Column('size_bytes', sa.BIGINT(), nullable=False),
    sa.Column('extracted_text', sa.Text(), nullable=True),
    sa.Column('domain', sa.String(length=50), nullable=True),
    sa.Column('domain_confidence', sa.Float(), nullable=True),
    sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_checksum_sha256'), 'documents', ['checksum_sha256'], unique=False)
    op.create_index(op.f('ix_documents_domain'), 'documents', ['domain'], unique=False)
    op.create_index('ix_documents_user_created', 'documents', ['user_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
    op.drop_index('ix_documents_user_created', table_name='documents')
    op.drop_index(op.f('ix_documents_domain'), table_name='documents')
    op.drop_index(op.f('ix_documents_checksum_sha256'), table_name='documents')
    op.drop_table('documents')
