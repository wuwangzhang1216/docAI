"""Add doctor-created patient and doctor AI conversation features

Revision ID: 006_add_doctor_patient_features
Revises: 005_add_generated_reports
Create Date: 2024-01-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_doctor_patient_features'
down_revision = '005_add_generated_reports'
branch_labels = None
depends_on = None


def table_exists(table_name, conn):
    """Check if a table exists."""
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name, conn):
    """Check if a column exists in a table."""
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    conn = op.get_bind()

    # Add password_must_change column to users table
    if not column_exists('users', 'password_must_change', conn):
        op.add_column(
            'users',
            sa.Column('password_must_change', sa.Boolean(), nullable=True, default=False)
        )
        # Set default value for existing rows
        op.execute("UPDATE users SET password_must_change = 0 WHERE password_must_change IS NULL")

    # Add created_by_doctor_id column to users table
    if not column_exists('users', 'created_by_doctor_id', conn):
        op.add_column(
            'users',
            sa.Column('created_by_doctor_id', sa.String(36), nullable=True)
        )
        # Note: SQLite doesn't support adding foreign key constraints to existing tables
        # The foreign key is defined in the model but won't be enforced at DB level for SQLite

    # Create doctor_conversations table
    if not table_exists('doctor_conversations', conn):
        op.create_table(
            'doctor_conversations',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('doctor_id', sa.String(36), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('messages_json', sa.Text(), nullable=True, default='[]'),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True, index=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Drop doctor_conversations table
    if table_exists('doctor_conversations', conn):
        op.drop_table('doctor_conversations')

    # Remove created_by_doctor_id column from users table
    if column_exists('users', 'created_by_doctor_id', conn):
        op.drop_column('users', 'created_by_doctor_id')

    # Remove password_must_change column from users table
    if column_exists('users', 'password_must_change', conn):
        op.drop_column('users', 'password_must_change')
