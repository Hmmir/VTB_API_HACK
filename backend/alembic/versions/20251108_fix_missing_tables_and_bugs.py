"""Fix missing tables and bugs

Revision ID: 20251108_fix_missing
Revises: add_family_hub
Create Date: 2025-11-08 03:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251108_fix_missing'
down_revision = 'add_family_hub'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old producttype enum and bank_products table, recreate with correct values
    op.execute("DROP TABLE IF EXISTS bank_products CASCADE")
    op.execute("DROP TYPE IF EXISTS producttype CASCADE")
    op.execute("""
        CREATE TYPE producttype AS ENUM ('deposit', 'credit', 'card', 'loan', 'mortgage');
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE agreementstatus AS ENUM ('draft', 'active', 'suspended', 'closed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymentscheduletype AS ENUM ('annuity', 'differentiated', 'bullet', 'custom');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create product_agreements table
    op.create_table('product_agreements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bank_product_id', sa.String(length=255), nullable=True),
        sa.Column('agreement_number', sa.String(length=50), nullable=False),
        sa.Column('product_type', postgresql.ENUM('deposit', 'credit', 'card', 'loan', 'mortgage', name='producttype', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'suspended', 'closed', 'cancelled', name='agreementstatus', create_type=False), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('interest_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('term_months', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('signed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('payment_schedule_type', postgresql.ENUM('annuity', 'differentiated', 'bullet', 'custom', name='paymentscheduletype', create_type=False), nullable=True),
        sa.Column('monthly_payment', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('outstanding_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('accumulated_interest', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('card_number_masked', sa.String(length=20), nullable=True),
        sa.Column('credit_limit', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('available_limit', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('linked_account_id', sa.Integer(), nullable=True),
        sa.Column('agreement_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['linked_account_id'], ['accounts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agreement_number')
    )
    op.create_index(op.f('ix_product_agreements_user_id'), 'product_agreements', ['user_id'], unique=False)
    op.create_index(op.f('ix_product_agreements_product_type'), 'product_agreements', ['product_type'], unique=False)
    op.create_index(op.f('ix_product_agreements_status'), 'product_agreements', ['status'], unique=False)

    # Create payment_schedules table
    op.create_table('payment_schedules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('agreement_id', sa.String(length=36), nullable=False),
        sa.Column('payment_number', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('principal_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('interest_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('paid_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('is_paid', sa.Boolean(), nullable=False),
        sa.Column('is_overdue', sa.Boolean(), nullable=False),
        sa.Column('payment_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['product_agreements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_schedules_agreement_id'), 'payment_schedules', ['agreement_id'], unique=False)
    op.create_index(op.f('ix_payment_schedules_due_date'), 'payment_schedules', ['due_date'], unique=False)

    # Create agreement_events table
    op.create_table('agreement_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('agreement_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['product_agreements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agreement_events_agreement_id'), 'agreement_events', ['agreement_id'], unique=False)
    op.create_index(op.f('ix_agreement_events_timestamp'), 'agreement_events', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_agreement_events_timestamp'), table_name='agreement_events')
    op.drop_index(op.f('ix_agreement_events_agreement_id'), table_name='agreement_events')
    op.drop_table('agreement_events')
    
    op.drop_index(op.f('ix_payment_schedules_due_date'), table_name='payment_schedules')
    op.drop_index(op.f('ix_payment_schedules_agreement_id'), table_name='payment_schedules')
    op.drop_table('payment_schedules')
    
    op.drop_index(op.f('ix_product_agreements_status'), table_name='product_agreements')
    op.drop_index(op.f('ix_product_agreements_product_type'), table_name='product_agreements')
    op.drop_index(op.f('ix_product_agreements_user_id'), table_name='product_agreements')
    op.drop_table('product_agreements')
    
    # Drop enums
    sa.Enum(name='paymentscheduletype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='agreementstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='producttype').drop(op.get_bind(), checkfirst=True)

