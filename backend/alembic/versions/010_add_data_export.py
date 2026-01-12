"""Add data export tables

Revision ID: 010_add_data_export
Revises: 009_add_appointments
Create Date: 2024-01-20 00:00:00.000000

This migration adds the data_export_requests table for patient data portability.

Features:
- Patient can request export of their data
- Supports JSON, CSV (ZIP), and PDF summary formats
- Secure download with tokens and expiration
- Rate limiting (1 export per 24h)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_add_data_export'
down_revision = '009_add_appointments'
branch_labels = None
depends_on = None


def table_exists(table_name, conn):
    """Check if a table exists."""
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    conn = op.get_bind()

    # ============================================
    # Data Export Requests Table
    # ============================================
    if not table_exists('data_export_requests', conn):
        op.create_table(
            'data_export_requests',
            # Primary key (UUID)
            sa.Column('id', sa.String(36), primary_key=True),

            # Requester
            sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),

            # Export configuration
            sa.Column('export_format', sa.String(20), default='JSON', nullable=False),

            # Data selection
            sa.Column('include_profile', sa.Boolean(), default=True),
            sa.Column('include_checkins', sa.Boolean(), default=True),
            sa.Column('include_assessments', sa.Boolean(), default=True),
            sa.Column('include_conversations', sa.Boolean(), default=True),
            sa.Column('include_messages', sa.Boolean(), default=True),

            # Date range (optional)
            sa.Column('date_from', sa.DateTime(), nullable=True),
            sa.Column('date_to', sa.DateTime(), nullable=True),

            # Processing status
            sa.Column('status', sa.String(20), default='PENDING', nullable=False),
            sa.Column('progress_percent', sa.Integer(), default=0),
            sa.Column('error_message', sa.Text(), nullable=True),

            # File information
            sa.Column('s3_key', sa.String(500), nullable=True),
            sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
            sa.Column('file_checksum', sa.String(64), nullable=True),

            # Download security
            sa.Column('download_token', sa.String(64), unique=True, nullable=True),
            sa.Column('download_expires_at', sa.DateTime(), nullable=True),
            sa.Column('download_count', sa.Integer(), default=0),
            sa.Column('max_downloads', sa.Integer(), default=3),

            # Timestamps
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('processing_started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('last_downloaded_at', sa.DateTime(), nullable=True),

            # Request metadata
            sa.Column('request_ip', sa.String(45), nullable=True),
            sa.Column('user_agent', sa.String(500), nullable=True),
        )

        # Create indexes
        op.create_index('ix_data_export_requests_patient_id', 'data_export_requests', ['patient_id'])
        op.create_index('ix_data_export_requests_status', 'data_export_requests', ['status'])
        op.create_index('ix_data_export_requests_download_token', 'data_export_requests', ['download_token'])
        op.create_index('ix_data_export_requests_created_at', 'data_export_requests', ['created_at'])


def downgrade() -> None:
    conn = op.get_bind()

    if table_exists('data_export_requests', conn):
        op.drop_table('data_export_requests')
