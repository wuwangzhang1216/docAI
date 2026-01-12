"""Add appointments table

Revision ID: 009_add_appointments
Revises: 008_add_email_system
Create Date: 2024-01-19 00:00:00.000000

This migration adds the appointments table for scheduling
doctor-patient consultations.

Features:
- Schedule appointments between doctors and patients
- Track appointment status (pending, confirmed, completed, cancelled, no_show)
- Link to pre-visit summaries
- Support for appointment reminders
- Cancellation tracking
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009_add_appointments'
down_revision = '008_add_email_system'
branch_labels = None
depends_on = None


def table_exists(table_name, conn):
    """Check if a table exists."""
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def index_exists(index_name, table_name, conn):
    """Check if an index exists."""
    inspector = sa.inspect(conn)
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def upgrade() -> None:
    conn = op.get_bind()

    # ============================================
    # Appointments Table
    # ============================================
    if not table_exists('appointments', conn):
        op.create_table(
            'appointments',
            # Primary key (UUID)
            sa.Column('id', sa.String(36), primary_key=True),

            # Foreign keys
            sa.Column('doctor_id', sa.String(36), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False),
            sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
            sa.Column('pre_visit_summary_id', sa.String(36), sa.ForeignKey('pre_visit_summaries.id', ondelete='SET NULL'), nullable=True),

            # Scheduling
            sa.Column('appointment_date', sa.Date(), nullable=False),
            sa.Column('start_time', sa.Time(), nullable=False),
            sa.Column('end_time', sa.Time(), nullable=False),

            # Appointment details
            sa.Column('appointment_type', sa.String(20), default='FOLLOW_UP', nullable=False),
            sa.Column('status', sa.String(20), default='PENDING', nullable=False),

            # Reason and notes
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('patient_notes', sa.Text(), nullable=True),

            # Reminders
            sa.Column('reminder_24h_sent', sa.Boolean(), default=False),
            sa.Column('reminder_1h_sent', sa.Boolean(), default=False),

            # Cancellation info
            sa.Column('cancelled_by', sa.String(20), nullable=True),
            sa.Column('cancel_reason', sa.Text(), nullable=True),
            sa.Column('cancelled_at', sa.DateTime(), nullable=True),

            # Completion info
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('completion_notes', sa.Text(), nullable=True),

            # Timestamps
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

        # Create indexes for common queries
        op.create_index('ix_appointments_doctor_id', 'appointments', ['doctor_id'])
        op.create_index('ix_appointments_patient_id', 'appointments', ['patient_id'])
        op.create_index('ix_appointments_appointment_date', 'appointments', ['appointment_date'])
        op.create_index('ix_appointments_status', 'appointments', ['status'])

        # Composite indexes for calendar views
        op.create_index('ix_appointments_doctor_date', 'appointments', ['doctor_id', 'appointment_date'])
        op.create_index('ix_appointments_patient_date', 'appointments', ['patient_id', 'appointment_date'])
        op.create_index('ix_appointments_status_date', 'appointments', ['status', 'appointment_date'])


def downgrade() -> None:
    conn = op.get_bind()

    if table_exists('appointments', conn):
        op.drop_table('appointments')
