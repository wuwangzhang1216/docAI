"""Add MFA tables

Revision ID: 011_add_mfa_tables
Revises: 010_add_data_export
Create Date: 2025-01-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '011_add_mfa_tables'
down_revision: Union[str, None] = '010_add_data_export'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_mfa table
    op.create_table(
        'user_mfa',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('totp_secret', sa.String(32), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('backup_codes_hash', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('enabled_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create mfa_backup_codes table
    op.create_table(
        'mfa_backup_codes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_mfa_id', sa.String(), nullable=False),
        sa.Column('code_hash', sa.String(128), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, default=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_mfa_id'], ['user_mfa.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_user_mfa_user_id', 'user_mfa', ['user_id'])
    op.create_index('ix_mfa_backup_codes_user_mfa_id', 'mfa_backup_codes', ['user_mfa_id'])


def downgrade() -> None:
    op.drop_index('ix_mfa_backup_codes_user_mfa_id', table_name='mfa_backup_codes')
    op.drop_index('ix_user_mfa_user_id', table_name='user_mfa')
    op.drop_table('mfa_backup_codes')
    op.drop_table('user_mfa')
