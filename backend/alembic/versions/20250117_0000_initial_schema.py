"""Initial schema

Revision ID: 20250117_0000
Revises:
Create Date: 2025-01-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250117_0000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create analysis_requests table
    op.create_table(
        'analysis_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='analysisstatus'), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Create indexes for analysis_requests
    op.create_index('ix_analysis_requests_url', 'analysis_requests', ['url'])
    op.create_index('ix_analysis_requests_status', 'analysis_requests', ['status'])

    # Create analysis_results table
    op.create_table(
        'analysis_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('page_html', sa.Text(), nullable=True),
        sa.Column('page_text', sa.Text(), nullable=True),
        sa.Column('screenshot_path', sa.String(length=512), nullable=True),
        sa.Column('seo_score', sa.Float(), nullable=True),
        sa.Column('seo_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('aeo_score', sa.Float(), nullable=True),
        sa.Column('aeo_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('analysis_duration', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['request_id'], ['analysis_requests.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('analysis_results')
    op.drop_index('ix_analysis_requests_status', 'analysis_requests')
    op.drop_index('ix_analysis_requests_url', 'analysis_requests')
    op.drop_table('analysis_requests')

    # Drop enum type
    sa.Enum(name='analysisstatus').drop(op.get_bind(), checkfirst=True)
