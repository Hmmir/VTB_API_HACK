"""Fix all enum values to lowercase

Revision ID: fix_all_enums
Revises: fix_product_type_enum
Create Date: 2025-11-06 02:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_all_enums'
down_revision = 'fix_product_type_enum'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix agreementstatus enum
    op.execute("CREATE TYPE agreementstatus_new AS ENUM ('draft', 'active', 'suspended', 'closed', 'cancelled')")
    op.execute("""
        ALTER TABLE product_agreements 
        ALTER COLUMN status TYPE agreementstatus_new 
        USING (
            CASE status::text
                WHEN 'DRAFT' THEN 'draft'::agreementstatus_new
                WHEN 'ACTIVE' THEN 'active'::agreementstatus_new
                WHEN 'SUSPENDED' THEN 'suspended'::agreementstatus_new
                WHEN 'CLOSED' THEN 'closed'::agreementstatus_new
                WHEN 'CANCELLED' THEN 'cancelled'::agreementstatus_new
                ELSE 'draft'::agreementstatus_new
            END
        )
    """)
    op.execute("DROP TYPE agreementstatus")
    op.execute("ALTER TYPE agreementstatus_new RENAME TO agreementstatus")
    
    # Fix paymentscheduletype enum
    op.execute("CREATE TYPE paymentscheduletype_new AS ENUM ('annuity', 'differentiated', 'bullet', 'custom')")
    op.execute("""
        ALTER TABLE product_agreements 
        ALTER COLUMN payment_schedule_type TYPE paymentscheduletype_new 
        USING (
            CASE payment_schedule_type::text
                WHEN 'ANNUITY' THEN 'annuity'::paymentscheduletype_new
                WHEN 'DIFFERENTIATED' THEN 'differentiated'::paymentscheduletype_new
                WHEN 'BULLET' THEN 'bullet'::paymentscheduletype_new
                WHEN 'CUSTOM' THEN 'custom'::paymentscheduletype_new
                ELSE NULL
            END
        )
    """)
    op.execute("DROP TYPE paymentscheduletype")
    op.execute("ALTER TYPE paymentscheduletype_new RENAME TO paymentscheduletype")


def downgrade() -> None:
    # Reverse agreementstatus
    op.execute("CREATE TYPE agreementstatus_old AS ENUM ('DRAFT', 'ACTIVE', 'SUSPENDED', 'CLOSED', 'CANCELLED')")
    op.execute("""
        ALTER TABLE product_agreements 
        ALTER COLUMN status TYPE agreementstatus_old 
        USING (
            CASE status::text
                WHEN 'draft' THEN 'DRAFT'::agreementstatus_old
                WHEN 'active' THEN 'ACTIVE'::agreementstatus_old
                WHEN 'suspended' THEN 'SUSPENDED'::agreementstatus_old
                WHEN 'closed' THEN 'CLOSED'::agreementstatus_old
                WHEN 'cancelled' THEN 'CANCELLED'::agreementstatus_old
                ELSE 'DRAFT'::agreementstatus_old
            END
        )
    """)
    op.execute("DROP TYPE agreementstatus")
    op.execute("ALTER TYPE agreementstatus_old RENAME TO agreementstatus")
    
    # Reverse paymentscheduletype
    op.execute("CREATE TYPE paymentscheduletype_old AS ENUM ('ANNUITY', 'DIFFERENTIATED', 'BULLET', 'CUSTOM')")
    op.execute("""
        ALTER TABLE product_agreements 
        ALTER COLUMN payment_schedule_type TYPE paymentscheduletype_old 
        USING (
            CASE payment_schedule_type::text
                WHEN 'annuity' THEN 'ANNUITY'::paymentscheduletype_old
                WHEN 'differentiated' THEN 'DIFFERENTIATED'::paymentscheduletype_old
                WHEN 'bullet' THEN 'BULLET'::paymentscheduletype_old
                WHEN 'custom' THEN 'CUSTOM'::paymentscheduletype_old
                ELSE NULL
            END
        )
    """)
    op.execute("DROP TYPE paymentscheduletype")
    op.execute("ALTER TYPE paymentscheduletype_old RENAME TO paymentscheduletype")

