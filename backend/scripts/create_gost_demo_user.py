"""
Create GOST demo user for hackathon demonstration.
Usage: python /app/scripts/create_gost_demo_user.py
"""
import sys
import os
sys.path.insert(0, '/app')

from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.utils.security import hash_password

def create_gost_user():
    """Create GOST demo user."""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == "team075-demo@financehub.ru").first()
        
        if existing_user:
            print("❌ GOST demo user already exists!")
            print(f"📧 Email: team075-demo@financehub.ru")
            print(f"🔑 Password: gost2024")
            return
        
        # Create GOST demo user
        hashed_password = hash_password("gost2024")
        
        gost_user = User(
            email="team075-demo@financehub.ru",
            hashed_password=hashed_password,
            full_name="GOST Demo User",
            phone="+7 (999) 123-45-67",
            use_gost_mode=True  # GOST режим включен
        )
        
        db.add(gost_user)
        db.commit()
        db.refresh(gost_user)
        
        print("✅ GOST demo user created successfully!")
        print(f"📧 Email: team075-demo@financehub.ru")
        print(f"🔑 Password: gost2024")
        print(f"🔒 GOST Mode: Enabled")
        
    except Exception as e:
        print(f"❌ Error creating GOST user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_gost_user()

