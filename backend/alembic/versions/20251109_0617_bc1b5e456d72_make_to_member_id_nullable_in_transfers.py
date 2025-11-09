"""make_to_member_id_nullable_in_transfers

Revision ID: bc1b5e456d72
Revises: c98a86d19d57
Create Date: 2025-11-09 06:17:43.163813

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc1b5e456d72'
down_revision = 'c98a86d19d57'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make to_member_id nullable in family_transfers table
    op.alter_column('family_transfers', 'to_member_id',
                    existing_type=sa.Integer(),
                    nullable=True)


def downgrade() -> None:
    # Revert to_member_id to not nullable
    op.alter_column('family_transfers', 'to_member_id',
                    existing_type=sa.Integer(),
                    nullable=False)

