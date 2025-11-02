"""add consent management tables

Revision ID: b1e3b4c1a2f3
Revises: a528b48e4484
Create Date: 2025-11-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b1e3b4c1a2f3'
down_revision = 'a528b48e4484'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    consent_status_enum = sa.Enum(
        'requested', 'approved', 'active', 'revoked', 'expired', 'rejected',
        name='consentstatus'
    )
    consent_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create partner_banks table
    op.create_table(
        'partner_banks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('code', sa.String(length=50), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('api_endpoint', sa.String(length=512), nullable=True),
        sa.Column('jwks_uri', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create consent_requests table
    op.create_table(
        'consent_requests',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('partner_bank_id', sa.String(length=36), sa.ForeignKey('partner_banks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scopes', sa.JSON(), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('status', consent_status_enum, nullable=False, server_default='requested'),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('requested_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
    )
    
    # Create consents table
    op.create_table(
        'consents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('request_id', sa.String(length=36), sa.ForeignKey('consent_requests.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('partner_bank_id', sa.String(length=36), sa.ForeignKey('partner_banks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scopes', sa.JSON(), nullable=False),
        sa.Column('status', consent_status_enum, nullable=False, server_default='active', index=True),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('valid_until', sa.DateTime(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
    )
    
    # Create consent_events table
    op.create_table(
        'consent_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('consent_id', sa.String(length=36), sa.ForeignKey('consents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )


def downgrade() -> None:
    op.drop_table('consent_events')
    op.drop_table('consents')
    op.drop_table('consent_requests')
    op.drop_table('partner_banks')
    
    # Drop enum type
    sa.Enum(name='consentstatus').drop(op.get_bind(), checkfirst=True)

