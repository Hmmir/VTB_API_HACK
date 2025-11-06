"""Fix product type enum values

Revision ID: fix_product_type_enum
Revises: 001_initial
Create Date: 2025-11-06 02:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_product_type_enum'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Create new enum type with correct values
    op.execute("CREATE TYPE producttype_new AS ENUM ('deposit', 'credit', 'card', 'loan', 'mortgage')")
    
    # Step 2: Update product_agreements table to use new enum
    op.execute("""
        ALTER TABLE product_agreements 
        ALTER COLUMN product_type TYPE producttype_new 
        USING (
            CASE product_type::text
                WHEN 'DEPOSIT' THEN 'deposit'::producttype_new
                WHEN 'LOAN' THEN 'loan'::producttype_new
                WHEN 'CREDIT_CARD' THEN 'card'::producttype_new
                WHEN 'INVESTMENT' THEN 'deposit'::producttype_new
                ELSE 'deposit'::producttype_new
            END
        )
    """)
    
    # Step 3: Update bank_products table to use new enum
    op.execute("""
        ALTER TABLE bank_products 
        ALTER COLUMN product_type TYPE producttype_new 
        USING (
            CASE product_type::text
                WHEN 'DEPOSIT' THEN 'deposit'::producttype_new
                WHEN 'LOAN' THEN 'loan'::producttype_new
                WHEN 'CREDIT_CARD' THEN 'card'::producttype_new
                WHEN 'INVESTMENT' THEN 'deposit'::producttype_new
                ELSE 'deposit'::producttype_new
            END
        )
    """)
    
    # Step 4: Drop old enum type
    op.execute("DROP TYPE producttype")
    
    # Step 5: Rename new enum type to original name
    op.execute("ALTER TYPE producttype_new RENAME TO producttype")


def downgrade() -> None:
    # Reverse the changes
    op.execute("CREATE TYPE producttype_old AS ENUM ('DEPOSIT', 'LOAN', 'CREDIT_CARD', 'INVESTMENT')")
    
    op.execute("""
        ALTER TABLE product_agreements 
        ALTER COLUMN product_type TYPE producttype_old 
        USING (
            CASE product_type::text
                WHEN 'deposit' THEN 'DEPOSIT'::producttype_old
                WHEN 'loan' THEN 'LOAN'::producttype_old
                WHEN 'card' THEN 'CREDIT_CARD'::producttype_old
                WHEN 'credit' THEN 'LOAN'::producttype_old
                WHEN 'mortgage' THEN 'LOAN'::producttype_old
                ELSE 'DEPOSIT'::producttype_old
            END
        )
    """)
    
    op.execute("""
        ALTER TABLE bank_products 
        ALTER COLUMN product_type TYPE producttype_old 
        USING (
            CASE product_type::text
                WHEN 'deposit' THEN 'DEPOSIT'::producttype_old
                WHEN 'loan' THEN 'LOAN'::producttype_old
                WHEN 'card' THEN 'CREDIT_CARD'::producttype_old
                WHEN 'credit' THEN 'LOAN'::producttype_old
                WHEN 'mortgage' THEN 'LOAN'::producttype_old
                ELSE 'DEPOSIT'::producttype_old
            END
        )
    """)
    
    op.execute("DROP TYPE producttype")
    op.execute("ALTER TYPE producttype_old RENAME TO producttype")

