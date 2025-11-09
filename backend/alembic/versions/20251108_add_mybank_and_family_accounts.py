"""Add MyBank support and family accounts

Revision ID: add_mybank_family
Revises: 20251108_fix_missing
Create Date: 2025-11-08 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_mybank_family'
down_revision = '20251108_fix_missing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'mybank' to BankProvider enum
    op.execute("""
        ALTER TYPE bankprovider ADD VALUE IF NOT EXISTS 'mybank';
    """)
    
    # Family shared accounts - tracks which accounts are shared with family
    op.create_table(
        'family_shared_accounts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('family_id', sa.Integer(), sa.ForeignKey('family_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', sa.Integer(), sa.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_type', sa.String(50), nullable=False),  # 'personal', 'family_wallet'
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('family_id', 'account_id', name='uq_family_account')
    )
    op.create_index('ix_family_shared_accounts_family_id', 'family_shared_accounts', ['family_id'])
    
    # Member card mapping - which cards/accounts member shares with family
    op.create_table(
        'family_member_accounts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('family_id', sa.Integer(), sa.ForeignKey('family_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('member_id', sa.Integer(), sa.ForeignKey('family_members.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', sa.Integer(), sa.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('family_id', 'member_id', 'account_id', name='uq_family_member_account')
    )
    op.create_index('ix_family_member_accounts_family_id', 'family_member_accounts', ['family_id'])
    op.create_index('ix_family_member_accounts_member_id', 'family_member_accounts', ['member_id'])
    
    # Link family goals to real MyBank accounts
    op.add_column('family_goals', sa.Column('external_goal_id', sa.String(100), nullable=True))
    op.add_column('family_goals', sa.Column('linked_account_id', sa.Integer(), sa.ForeignKey('accounts.id'), nullable=True))
    op.create_index('ix_family_goals_linked_account', 'family_goals', ['linked_account_id'])
    
    # Track real transactions for goal contributions
    # source_account_id already exists in add_family_hub migration
    op.add_column('family_goal_contributions', sa.Column('external_tx_id', sa.String(100), nullable=True))


def downgrade() -> None:
    # source_account_id is managed by add_family_hub migration
    op.drop_column('family_goal_contributions', 'external_tx_id')
    
    op.drop_index('ix_family_goals_linked_account', table_name='family_goals')
    op.drop_column('family_goals', 'linked_account_id')
    op.drop_column('family_goals', 'external_goal_id')
    
    op.drop_index('ix_family_member_accounts_member_id', table_name='family_member_accounts')
    op.drop_index('ix_family_member_accounts_family_id', table_name='family_member_accounts')
    op.drop_table('family_member_accounts')
    
    op.drop_index('ix_family_shared_accounts_family_id', table_name='family_shared_accounts')
    op.drop_table('family_shared_accounts')
    
    # Note: Cannot remove enum value in PostgreSQL, requires recreation

