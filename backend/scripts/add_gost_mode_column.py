"""
Add use_gost_mode column to users table.
Usage: python /app/scripts/add_gost_mode_column.py
"""
import sys
sys.path.insert(0, '/app')

from sqlalchemy import text
from app.database import engine

def add_gost_mode_column():
    """Add use_gost_mode column to users table."""
    with engine.connect() as conn:
        try:
            # Add column if it doesn't exist
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS use_gost_mode BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            print("✅ Column 'use_gost_mode' added successfully!")
        except Exception as e:
            print(f"❌ Error adding column: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_gost_mode_column()


