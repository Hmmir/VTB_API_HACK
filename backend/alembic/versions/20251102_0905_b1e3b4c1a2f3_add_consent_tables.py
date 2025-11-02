"""add consent and partner bank tables

Revision ID: b1e3b4c1a2f3
Revises: a528b48e4484
Create Date: 2025-11-02 09:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1e3b4c1a2f3'
down_revision = 'a528b48e4484'
branch_labels = None
depends_on = None


def upgrade() -> None:
    partner_bank_status = sa.Enum('active', 'inactive', name='partnerbankstatus')
    consent_request_status = sa.Enum('requested', 'approved', 'rejected', 'expired', name='consentrequeststatus')
    consent_status = sa.Enum('active', 'revoked', 'expired', name='consentstatus')
    consent_event_type = sa.Enum('requested', 'approved', 'rejected', 'activated', 'expired', 'revoked', 'usage', name='consenteventtype')

    bind = op.get_bind()
    partner_bank_status.create(bind, checkfirst=True)
    consent_request_status.create(bind, checkfirst=True)
    consent_status.create(bind, checkfirst=True)
    consent_event_type.create(bind, checkfirst=True)

    op.create_table(
        'partner_banks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('code', sa.String(length=50), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('jwks_uri', sa.String(length=500), nullable=True),
        sa.Column('callback_url', sa.String(length=500), nullable=True),
        sa.Column('status', partner_bank_status, nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_partner_banks_code', 'partner_banks', ['code'], unique=True)

    op.create_table(
        'consent_requests',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('requesting_bank_id', sa.String(length=36), sa.ForeignKey('partner_banks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requested_scopes', sa.JSON(), nullable=False),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('callback_url', sa.String(length=500), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('status', consent_request_status, nullable=False, server_default='requested'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_consent_requests_user_id', 'consent_requests', ['user_id'], unique=False)

    op.create_table(
        'consents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('request_id', sa.String(length=36), sa.ForeignKey('consent_requests.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('signature_hash', sa.String(length=512), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('status', consent_status, nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'consent_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('consent_id', sa.String(length=36), sa.ForeignKey('consents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('request_id', sa.String(length=36), sa.ForeignKey('consent_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', consent_event_type, nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_consent_events_consent_id', 'consent_events', ['consent_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_consent_events_consent_id', table_name='consent_events')
    op.drop_table('consent_events')

    op.drop_table('consents')

    op.drop_index('ix_consent_requests_user_id', table_name='consent_requests')
    op.drop_table('consent_requests')

    op.drop_index('ix_partner_banks_code', table_name='partner_banks')
    op.drop_table('partner_banks')

    partner_bank_status = sa.Enum('active', 'inactive', name='partnerbankstatus')
    consent_request_status = sa.Enum('requested', 'approved', 'rejected', 'expired', name='consentrequeststatus')
    consent_status = sa.Enum('active', 'revoked', 'expired', name='consentstatus')
    consent_event_type = sa.Enum('requested', 'approved', 'rejected', 'activated', 'expired', 'revoked', 'usage', name='consenteventtype')

    bind = op.get_bind()
    consent_event_type.drop(bind, checkfirst=True)
    consent_status.drop(bind, checkfirst=True)
    consent_request_status.drop(bind, checkfirst=True)
    partner_bank_status.drop(bind, checkfirst=True)


