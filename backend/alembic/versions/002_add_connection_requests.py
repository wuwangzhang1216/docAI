"""Add patient connection requests table

Revision ID: 002_add_connection_requests
Revises: 001_add_patient_profile
Create Date: 2024-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_connection_requests'
down_revision: Union[str, None] = '001_add_patient_profile'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create patient_connection_requests table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'patient_connection_requests' not in existing_tables:
        op.create_table(
            'patient_connection_requests',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('doctor_id', sa.String(36), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False),
            sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
            sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED', name='connectionstatus'), nullable=False, default='PENDING'),
            sa.Column('message', sa.Text, nullable=True),
            sa.Column('created_at', sa.DateTime, nullable=True),
            sa.Column('updated_at', sa.DateTime, nullable=True),
            sa.Column('responded_at', sa.DateTime, nullable=True),
        )

        # Create indexes
        op.create_index('ix_patient_connection_requests_doctor_id', 'patient_connection_requests', ['doctor_id'])
        op.create_index('ix_patient_connection_requests_patient_id', 'patient_connection_requests', ['patient_id'])
        op.create_index('ix_patient_connection_requests_status', 'patient_connection_requests', ['status'])
        op.create_index('idx_pending_requests', 'patient_connection_requests', ['doctor_id', 'patient_id', 'status'])


def downgrade() -> None:
    """Drop patient_connection_requests table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'patient_connection_requests' in existing_tables:
        op.drop_index('idx_pending_requests', table_name='patient_connection_requests')
        op.drop_index('ix_patient_connection_requests_status', table_name='patient_connection_requests')
        op.drop_index('ix_patient_connection_requests_patient_id', table_name='patient_connection_requests')
        op.drop_index('ix_patient_connection_requests_doctor_id', table_name='patient_connection_requests')
        op.drop_table('patient_connection_requests')
