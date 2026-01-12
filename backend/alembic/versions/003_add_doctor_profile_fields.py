"""Add doctor profile fields

Revision ID: 003_add_doctor_profile
Revises: 002_add_connection_requests
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_doctor_profile'
down_revision = '002_add_connection_requests'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to doctors table
    op.add_column('doctors', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('doctors', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('doctors', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('doctors', sa.Column('years_of_experience', sa.String(10), nullable=True))
    op.add_column('doctors', sa.Column('education', sa.Text(), nullable=True))
    op.add_column('doctors', sa.Column('languages', sa.String(255), nullable=True))
    op.add_column('doctors', sa.Column('clinic_name', sa.String(200), nullable=True))
    op.add_column('doctors', sa.Column('clinic_address', sa.String(255), nullable=True))
    op.add_column('doctors', sa.Column('clinic_city', sa.String(100), nullable=True))
    op.add_column('doctors', sa.Column('clinic_country', sa.String(100), nullable=True))
    op.add_column('doctors', sa.Column('consultation_hours', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('doctors', 'consultation_hours')
    op.drop_column('doctors', 'clinic_country')
    op.drop_column('doctors', 'clinic_city')
    op.drop_column('doctors', 'clinic_address')
    op.drop_column('doctors', 'clinic_name')
    op.drop_column('doctors', 'languages')
    op.drop_column('doctors', 'education')
    op.drop_column('doctors', 'years_of_experience')
    op.drop_column('doctors', 'bio')
    op.drop_column('doctors', 'phone')
    op.drop_column('doctors', 'updated_at')
