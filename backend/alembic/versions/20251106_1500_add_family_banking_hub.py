"""add family banking hub

Revision ID: add_family_hub
Revises: 001_initial
Create Date: 2025-11-06 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_family_hub'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums (skip if they already exist)
    op.execute("DO $$ BEGIN CREATE TYPE familyrole AS ENUM ('admin', 'member'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE familymemberstatus AS ENUM ('pending', 'active', 'blocked'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE familybudgetperiod AS ENUM ('weekly', 'monthly'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE familygoalstatus AS ENUM ('active', 'completed', 'archived'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE familytransferstatus AS ENUM ('pending', 'approved', 'rejected', 'executed'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE familynotificationtype AS ENUM (
                'limit_approach', 'limit_exceeded', 'budget_approach', 'budget_exceeded',
                'transfer_request', 'transfer_approved', 'transfer_rejected', 'transfer_executed',
                'goal_progress', 'goal_completed', 'member_joined', 'member_left'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create family_groups table
    op.create_table(
        'family_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('invite_code', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_groups_id'), 'family_groups', ['id'], unique=False)
    op.create_index(op.f('ix_family_groups_invite_code'), 'family_groups', ['invite_code'], unique=True)
    
    # Create family_members table
    op.create_table(
        'family_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('family_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', postgresql.ENUM('admin', 'member', name='familyrole', create_type=False), nullable=False, server_default='member'),
        sa.Column('status', postgresql.ENUM('pending', 'active', 'blocked', name='familymemberstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['family_id'], ['family_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_members_id'), 'family_members', ['id'], unique=False)
    op.create_index(op.f('ix_family_members_family_id'), 'family_members', ['family_id'], unique=False)
    op.create_index(op.f('ix_family_members_user_id'), 'family_members', ['user_id'], unique=False)
    op.create_index('idx_family_user', 'family_members', ['family_id', 'user_id'], unique=True)
    
    # Create family_member_settings table
    op.create_table(
        'family_member_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('show_accounts', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('default_visibility', sa.String(length=50), nullable=False, server_default='full'),
        sa.Column('custom_limits', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['member_id'], ['family_members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('member_id')
    )
    
    # Create family_budgets table
    op.create_table(
        'family_budgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('family_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('period', postgresql.ENUM('weekly', 'monthly', create_type=False, name='familybudgetperiod'), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['family_id'], ['family_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_budgets_id'), 'family_budgets', ['id'], unique=False)
    op.create_index(op.f('ix_family_budgets_family_id'), 'family_budgets', ['family_id'], unique=False)
    op.create_index(op.f('ix_family_budgets_category_id'), 'family_budgets', ['category_id'], unique=False)
    
    # Create family_member_limits table
    op.create_table(
        'family_member_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('family_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('period', postgresql.ENUM('weekly', 'monthly', create_type=False, name='familybudgetperiod'), nullable=False),
        sa.Column('auto_unlock', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['family_id'], ['family_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['family_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_limits_id'), 'family_member_limits', ['id'], unique=False)
    op.create_index(op.f('ix_family_member_limits_family_id'), 'family_member_limits', ['family_id'], unique=False)
    op.create_index(op.f('ix_family_member_limits_member_id'), 'family_member_limits', ['member_id'], unique=False)
    op.create_index(op.f('ix_family_member_limits_category_id'), 'family_member_limits', ['category_id'], unique=False)
    
    # Create family_goals table
    op.create_table(
        'family_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('family_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('current_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('status', postgresql.ENUM('active', 'completed', 'archived', create_type=False, name='familygoalstatus'), nullable=False, server_default='active'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['family_id'], ['family_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_goals_id'), 'family_goals', ['id'], unique=False)
    op.create_index(op.f('ix_family_goals_family_id'), 'family_goals', ['family_id'], unique=False)
    
    # Create family_goal_contributions table
    op.create_table(
        'family_goal_contributions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('source_account_id', sa.Integer(), nullable=True),
        sa.Column('scheduled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('schedule_rule', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['goal_id'], ['family_goals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['family_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_account_id'], ['accounts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_goal_contributions_id'), 'family_goal_contributions', ['id'], unique=False)
    op.create_index(op.f('ix_family_goal_contributions_goal_id'), 'family_goal_contributions', ['goal_id'], unique=False)
    op.create_index(op.f('ix_family_goal_contributions_member_id'), 'family_goal_contributions', ['member_id'], unique=False)
    
    # Create family_transfers table
    op.create_table(
        'family_transfers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('family_id', sa.Integer(), nullable=False),
        sa.Column('from_member_id', sa.Integer(), nullable=False),
        sa.Column('to_member_id', sa.Integer(), nullable=False),
        sa.Column('from_account_id', sa.Integer(), nullable=True),
        sa.Column('to_account_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='RUB'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', 'executed', create_type=False, name='familytransferstatus'), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['family_id'], ['family_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_member_id'], ['family_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_member_id'], ['family_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_account_id'], ['accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['to_account_id'], ['accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_transfers_id'), 'family_transfers', ['id'], unique=False)
    op.create_index(op.f('ix_family_transfers_family_id'), 'family_transfers', ['family_id'], unique=False)
    
    # Create family_notifications table
    op.create_table(
        'family_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('family_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=True),
        sa.Column('type', postgresql.ENUM(
            'limit_approach', 'limit_exceeded', 'budget_approach', 'budget_exceeded',
            'transfer_request', 'transfer_approved', 'transfer_rejected', 'transfer_executed',
            'goal_progress', 'goal_completed', 'member_joined', 'member_left',
            name='familynotificationtype', create_type=False
        ), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='new'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['family_id'], ['family_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['family_members.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_notifications_id'), 'family_notifications', ['id'], unique=False)
    op.create_index(op.f('ix_family_notifications_family_id'), 'family_notifications', ['family_id'], unique=False)
    op.create_index(op.f('ix_family_notifications_member_id'), 'family_notifications', ['member_id'], unique=False)
    
    # Create family_activity_log table
    op.create_table(
        'family_activity_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('family_id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target', sa.String(length=100), nullable=True),
        sa.Column('action_metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['family_id'], ['family_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_activity_log_id'), 'family_activity_log', ['id'], unique=False)
    op.create_index(op.f('ix_family_activity_log_family_id'), 'family_activity_log', ['family_id'], unique=False)
    op.create_index(op.f('ix_family_activity_log_timestamp'), 'family_activity_log', ['timestamp'], unique=False)
    
    # Add family banking columns to accounts table
    op.add_column('accounts', sa.Column('visibility_scope', sa.String(length=50), nullable=False, server_default='family'))
    op.add_column('accounts', sa.Column('family_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_accounts_family_id', 'accounts', 'family_groups', ['family_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_accounts_family_id'), 'accounts', ['family_id'], unique=False)


def downgrade() -> None:
    # Drop accounts columns
    op.drop_index(op.f('ix_accounts_family_id'), table_name='accounts')
    op.drop_constraint('fk_accounts_family_id', 'accounts', type_='foreignkey')
    op.drop_column('accounts', 'family_id')
    op.drop_column('accounts', 'visibility_scope')
    
    # Drop tables in reverse order
    op.drop_index(op.f('ix_family_activity_log_timestamp'), table_name='family_activity_log')
    op.drop_index(op.f('ix_family_activity_log_family_id'), table_name='family_activity_log')
    op.drop_index(op.f('ix_family_activity_log_id'), table_name='family_activity_log')
    op.drop_table('family_activity_log')
    
    op.drop_index(op.f('ix_family_notifications_member_id'), table_name='family_notifications')
    op.drop_index(op.f('ix_family_notifications_family_id'), table_name='family_notifications')
    op.drop_index(op.f('ix_family_notifications_id'), table_name='family_notifications')
    op.drop_table('family_notifications')
    
    op.drop_index(op.f('ix_family_transfers_family_id'), table_name='family_transfers')
    op.drop_index(op.f('ix_family_transfers_id'), table_name='family_transfers')
    op.drop_table('family_transfers')
    
    op.drop_index(op.f('ix_family_goal_contributions_member_id'), table_name='family_goal_contributions')
    op.drop_index(op.f('ix_family_goal_contributions_goal_id'), table_name='family_goal_contributions')
    op.drop_index(op.f('ix_family_goal_contributions_id'), table_name='family_goal_contributions')
    op.drop_table('family_goal_contributions')
    
    op.drop_index(op.f('ix_family_goals_family_id'), table_name='family_goals')
    op.drop_index(op.f('ix_family_goals_id'), table_name='family_goals')
    op.drop_table('family_goals')
    
    op.drop_index(op.f('ix_family_member_limits_category_id'), table_name='family_member_limits')
    op.drop_index(op.f('ix_family_member_limits_member_id'), table_name='family_member_limits')
    op.drop_index(op.f('ix_family_member_limits_family_id'), table_name='family_member_limits')
    op.drop_index(op.f('ix_family_member_limits_id'), table_name='family_member_limits')
    op.drop_table('family_member_limits')
    
    op.drop_index(op.f('ix_family_budgets_category_id'), table_name='family_budgets')
    op.drop_index(op.f('ix_family_budgets_family_id'), table_name='family_budgets')
    op.drop_index(op.f('ix_family_budgets_id'), table_name='family_budgets')
    op.drop_table('family_budgets')
    
    op.drop_table('family_member_settings')
    
    op.drop_index('idx_family_user', table_name='family_members')
    op.drop_index(op.f('ix_family_members_user_id'), table_name='family_members')
    op.drop_index(op.f('ix_family_members_family_id'), table_name='family_members')
    op.drop_index(op.f('ix_family_members_id'), table_name='family_members')
    op.drop_table('family_members')
    
    op.drop_index(op.f('ix_family_groups_invite_code'), table_name='family_groups')
    op.drop_index(op.f('ix_family_groups_id'), table_name='family_groups')
    op.drop_table('family_groups')
    
    # Drop enums
    op.execute("DROP TYPE familynotificationtype")
    op.execute("DROP TYPE familytransferstatus")
    op.execute("DROP TYPE familygoalstatus")
    op.execute("DROP TYPE familybudgetperiod")
    op.execute("DROP TYPE familymemberstatus")
    op.execute("DROP TYPE familyrole")

