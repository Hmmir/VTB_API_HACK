"""make_bank_connection_id_nullable

Revision ID: c98a86d19d57
Revises: fix_family_shared
Create Date: 2025-11-09 03:36:42.825051

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c98a86d19d57'
down_revision = 'fix_family_shared'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make bank_connection_id nullable in accounts table
    op.alter_column('accounts', 'bank_connection_id',
                    existing_type=sa.Integer(),
                    nullable=True)


def downgrade() -> None:
    # Revert bank_connection_id to not nullable
    op.alter_column('accounts', 'bank_connection_id',
                    existing_type=sa.Integer(),
                    nullable=False)

