"""Add email system tables

Revision ID: 008_add_email_system
Revises: 007_add_performance_indexes
Create Date: 2024-01-18 00:00:00.000000

This migration adds tables for the email notification system:
1. email_templates - Reusable email templates
2. email_logs - Email sending history and tracking
3. password_reset_tokens - Secure password reset tokens

Features:
- Patient invitation emails when doctors create accounts
- Password reset functionality
- Risk alert notifications to doctors
- Appointment reminders
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_add_email_system'
down_revision = '007_add_performance_indexes'
branch_labels = None
depends_on = None


def table_exists(table_name, conn):
    """Check if a table exists."""
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    conn = op.get_bind()

    # ============================================
    # Email Templates Table
    # ============================================
    if not table_exists('email_templates', conn):
        op.create_table(
            'email_templates',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('name', sa.String(100), unique=True, nullable=False),
            sa.Column('email_type', sa.String(50), nullable=False),
            sa.Column('subject', sa.String(255), nullable=False),
            sa.Column('body_html', sa.Text(), nullable=False),
            sa.Column('body_text', sa.Text(), nullable=True),
            sa.Column('language', sa.String(10), default='zh'),
            sa.Column('variables', sa.JSON(), nullable=True),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
        op.create_index('ix_email_templates_name', 'email_templates', ['name'])
        op.create_index('ix_email_templates_type', 'email_templates', ['email_type'])
        op.create_index('ix_email_templates_language', 'email_templates', ['language'])

    # ============================================
    # Email Logs Table
    # ============================================
    if not table_exists('email_logs', conn):
        op.create_table(
            'email_logs',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('template_id', sa.String(36), sa.ForeignKey('email_templates.id'), nullable=True),
            sa.Column('email_type', sa.String(50), nullable=False),

            # Recipient information
            sa.Column('recipient_email', sa.String(255), nullable=False),
            sa.Column('recipient_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('recipient_name', sa.String(100), nullable=True),

            # Sender information
            sa.Column('sender_email', sa.String(255), nullable=True),
            sa.Column('sender_name', sa.String(100), nullable=True),

            # Email content
            sa.Column('subject', sa.String(255), nullable=False),
            sa.Column('body_html', sa.Text(), nullable=True),
            sa.Column('body_text', sa.Text(), nullable=True),

            # Sending status
            sa.Column('status', sa.String(20), default='PENDING'),
            sa.Column('priority', sa.String(20), default='NORMAL'),

            # Retry information
            sa.Column('retry_count', sa.Integer(), default=0),
            sa.Column('max_retries', sa.Integer(), default=3),
            sa.Column('last_error', sa.Text(), nullable=True),

            # Related entity
            sa.Column('related_entity_type', sa.String(50), nullable=True),
            sa.Column('related_entity_id', sa.String(36), nullable=True),

            # Timestamps
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('queued_at', sa.DateTime(), nullable=True),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('failed_at', sa.DateTime(), nullable=True),

            # Metadata
            sa.Column('metadata', sa.JSON(), nullable=True),
        )
        op.create_index('ix_email_logs_type', 'email_logs', ['email_type'])
        op.create_index('ix_email_logs_status', 'email_logs', ['status'])
        op.create_index('ix_email_logs_recipient', 'email_logs', ['recipient_email'])
        op.create_index('ix_email_logs_created', 'email_logs', ['created_at'])
        op.create_index('ix_email_logs_status_priority', 'email_logs', ['status', 'priority'])
        op.create_index('ix_email_logs_created_status', 'email_logs', ['created_at', 'status'])

    # ============================================
    # Password Reset Tokens Table
    # ============================================
    if not table_exists('password_reset_tokens', conn):
        op.create_table(
            'password_reset_tokens',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('token', sa.String(64), unique=True, nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('used_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('request_ip', sa.String(45), nullable=True),
            sa.Column('user_agent', sa.String(500), nullable=True),
        )
        op.create_index('ix_password_reset_tokens_token', 'password_reset_tokens', ['token'])
        op.create_index('ix_password_reset_tokens_user', 'password_reset_tokens', ['user_id'])


def downgrade() -> None:
    conn = op.get_bind()

    # Drop tables in reverse order
    if table_exists('password_reset_tokens', conn):
        op.drop_table('password_reset_tokens')

    if table_exists('email_logs', conn):
        op.drop_table('email_logs')

    if table_exists('email_templates', conn):
        op.drop_table('email_templates')
