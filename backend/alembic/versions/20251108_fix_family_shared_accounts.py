"""Fix family_shared_accounts table

Revision ID: fix_family_shared
Revises: add_mybank_and_family
Create Date: 2025-11-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_family_shared'
down_revision = 'add_mybank_family'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old table if exists
    op.execute("DROP TABLE IF EXISTS family_shared_accounts CASCADE")
    
    # Create with correct schema
    op.create_table('family_shared_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('family_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('visibility', sa.Enum('FAMILY', 'PRIVATE', name='accountvisibility'), nullable=False, server_default='FAMILY'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['family_id'], ['family_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['family_members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('family_id', 'account_id', name='uq_family_account')
    )
    op.create_index('ix_family_shared_accounts_family_id', 'family_shared_accounts', ['family_id'])
    op.create_index('ix_family_shared_accounts_member_id', 'family_shared_accounts', ['member_id'])
    op.create_index('ix_family_shared_accounts_account_id', 'family_shared_accounts', ['account_id'])


def downgrade() -> None:
    op.drop_table('family_shared_accounts')

