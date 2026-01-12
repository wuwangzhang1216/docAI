"""Split full_name into first_name and last_name

Revision ID: 004_split_name_fields
Revises: 003_add_doctor_profile
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_split_name_fields'
down_revision = '003_add_doctor_profile'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name, conn):
    """Check if a column exists in a table."""
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    conn = op.get_bind()

    # Add first_name and last_name columns if they don't exist
    if not column_exists('patients', 'first_name', conn):
        op.add_column('patients', sa.Column('first_name', sa.String(50), nullable=True))
    if not column_exists('patients', 'last_name', conn):
        op.add_column('patients', sa.Column('last_name', sa.String(50), nullable=True))

    if not column_exists('doctors', 'first_name', conn):
        op.add_column('doctors', sa.Column('first_name', sa.String(50), nullable=True))
    if not column_exists('doctors', 'last_name', conn):
        op.add_column('doctors', sa.Column('last_name', sa.String(50), nullable=True))

    # Only migrate data if full_name column exists
    if column_exists('patients', 'full_name', conn):
        # Get all patients and split their names
        patients = conn.execute(sa.text("SELECT id, full_name FROM patients")).fetchall()
        for patient in patients:
            parts = patient.full_name.split(' ', 1) if patient.full_name else ['', '']
            first_name = parts[0] if parts else ''
            last_name = parts[1] if len(parts) > 1 else ''
            conn.execute(
                sa.text("UPDATE patients SET first_name = :first, last_name = :last WHERE id = :id"),
                {"first": first_name, "last": last_name, "id": patient.id}
            )

    if column_exists('doctors', 'full_name', conn):
        # Get all doctors and split their names
        doctors = conn.execute(sa.text("SELECT id, full_name FROM doctors")).fetchall()
        for doctor in doctors:
            parts = doctor.full_name.split(' ', 1) if doctor.full_name else ['', '']
            first_name = parts[0] if parts else ''
            last_name = parts[1] if len(parts) > 1 else ''
            conn.execute(
                sa.text("UPDATE doctors SET first_name = :first, last_name = :last WHERE id = :id"),
                {"first": first_name, "last": last_name, "id": doctor.id}
            )

    # Set default values for any NULL entries
    conn.execute(sa.text("UPDATE patients SET first_name = '' WHERE first_name IS NULL"))
    conn.execute(sa.text("UPDATE patients SET last_name = '' WHERE last_name IS NULL"))
    conn.execute(sa.text("UPDATE doctors SET first_name = '' WHERE first_name IS NULL"))
    conn.execute(sa.text("UPDATE doctors SET last_name = '' WHERE last_name IS NULL"))

    # Drop the old full_name columns if they exist
    # SQLite 3.35.0+ supports DROP COLUMN
    if column_exists('patients', 'full_name', conn):
        try:
            op.drop_column('patients', 'full_name')
        except Exception:
            pass

    if column_exists('doctors', 'full_name', conn):
        try:
            op.drop_column('doctors', 'full_name')
        except Exception:
            pass


def downgrade() -> None:
    conn = op.get_bind()

    # Add full_name columns back if they don't exist
    if not column_exists('patients', 'full_name', conn):
        op.add_column('patients', sa.Column('full_name', sa.String(100), nullable=True))
    if not column_exists('doctors', 'full_name', conn):
        op.add_column('doctors', sa.Column('full_name', sa.String(100), nullable=True))

    # Migrate data back: combine first_name and last_name into full_name
    if column_exists('patients', 'first_name', conn):
        conn.execute(sa.text("UPDATE patients SET full_name = first_name || ' ' || last_name"))
    if column_exists('doctors', 'first_name', conn):
        conn.execute(sa.text("UPDATE doctors SET full_name = first_name || ' ' || last_name"))

    # Drop first_name and last_name columns
    if column_exists('patients', 'first_name', conn):
        try:
            op.drop_column('patients', 'first_name')
        except Exception:
            pass
    if column_exists('patients', 'last_name', conn):
        try:
            op.drop_column('patients', 'last_name')
        except Exception:
            pass
    if column_exists('doctors', 'first_name', conn):
        try:
            op.drop_column('doctors', 'first_name')
        except Exception:
            pass
    if column_exists('doctors', 'last_name', conn):
        try:
            op.drop_column('doctors', 'last_name')
        except Exception:
            pass
