"""Add competitive analysis tables

Revision ID: 20250117_0001
Revises: 20250117_0000
Create Date: 2025-01-17 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250117_0001'
down_revision: Union[str, None] = '20250117_0000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create competitive_analysis_batches table
    op.create_table(
        'competitive_analysis_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='analysisstatus'), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('total_urls', sa.Integer(), nullable=False),
        sa.Column('completed_count', sa.Integer(), nullable=True),
        sa.Column('failed_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )

    # Create indexes for competitive_analysis_batches
    op.create_index('idx_batch_status_created', 'competitive_analysis_batches', ['status', 'created_at'])

    # Create competitive_analysis_urls table
    op.create_table(
        'competitive_analysis_urls',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('url_label', sa.String(length=255), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['competitive_analysis_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['request_id'], ['analysis_requests.id'], ondelete='CASCADE'),
    )

    # Create indexes for competitive_analysis_urls
    op.create_index('idx_batch_urls', 'competitive_analysis_urls', ['batch_id', 'order_index'])

    # Create comparison_results table
    op.create_table(
        'comparison_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('seo_comparison', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('aeo_comparison', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('market_leader', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('market_average', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('competitive_insights', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('opportunities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('threats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('comparison_duration', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['competitive_analysis_batches.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('comparison_results')
    op.drop_index('idx_batch_urls', 'competitive_analysis_urls')
    op.drop_table('competitive_analysis_urls')
    op.drop_index('idx_batch_status_created', 'competitive_analysis_batches')
    op.drop_table('competitive_analysis_batches')
