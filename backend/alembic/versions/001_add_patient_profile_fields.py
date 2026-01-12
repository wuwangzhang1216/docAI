"""Add patient profile fields

Revision ID: 001_add_patient_profile
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_patient_profile'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new patient profile columns."""
    # SQLite doesn't support ADD COLUMN IF NOT EXISTS, so we need to check manually
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('patients')]

    columns_to_add = [
        ('emergency_contact_relationship', sa.String(50)),
        ('updated_at', sa.DateTime),
        ('gender', sa.String(20)),
        ('preferred_language', sa.String(10)),
        ('address', sa.String(255)),
        ('city', sa.String(100)),
        ('country', sa.String(100)),
        ('current_medications', sa.Text),
        ('medical_conditions', sa.Text),
        ('allergies', sa.Text),
        ('therapy_history', sa.Text),
        ('mental_health_goals', sa.Text),
        ('support_system', sa.Text),
        ('triggers_notes', sa.Text),
        ('coping_strategies', sa.Text),
    ]

    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            op.add_column('patients', sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    """Remove patient profile columns."""
    # SQLite doesn't support DROP COLUMN easily, so this is a no-op
    # In production, you'd need to recreate the table
    pass
