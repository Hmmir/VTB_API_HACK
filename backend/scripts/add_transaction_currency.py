"""
Add currency column to transactions table.
Usage: python /app/scripts/add_transaction_currency.py
"""
import sys
sys.path.insert(0, '/app')

from sqlalchemy import text
from app.database import engine

def add_currency_column():
    """Add currency column to transactions table."""
    with engine.connect() as conn:
        try:
            # Add column if it doesn't exist
            conn.execute(text("""
                ALTER TABLE transactions 
                ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'RUB'
            """))
            conn.commit()
            print("✅ Column 'currency' added to transactions table!")
        except Exception as e:
            print(f"❌ Error adding column: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_currency_column()

