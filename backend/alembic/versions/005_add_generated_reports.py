"""Add generated_reports table

Revision ID: 005_add_generated_reports
Revises: 004_split_name_fields
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_generated_reports'
down_revision = '004_split_name_fields'
branch_labels = None
depends_on = None


def table_exists(table_name, conn):
    """Check if a table exists."""
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    conn = op.get_bind()

    if not table_exists('generated_reports', conn):
        op.create_table(
            'generated_reports',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('pre_visit_summary_id', sa.String(36), sa.ForeignKey('pre_visit_summaries.id', ondelete='SET NULL'), nullable=True),
            sa.Column('report_type', sa.String(50), nullable=False),
            sa.Column('s3_key', sa.String(255), nullable=False),
            sa.Column('generated_by_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('metadata_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True, index=True),
        )


def downgrade() -> None:
    conn = op.get_bind()

    if table_exists('generated_reports', conn):
        op.drop_table('generated_reports')
