#!/usr/bin/env python3
"""Create demo user for testing."""
import sys
sys.path.insert(0, '/app')

from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password

def main():
    db = SessionLocal()
    
    # Delete existing demo user if exists
    existing = db.query(User).filter(User.email == 'demo@financehub.ru').first()
    if existing:
        db.delete(existing)
        db.commit()
        print(f"🗑️ Удален существующий пользователь: {existing.email}")
    
    # Create new demo user
    user = User(
        email='demo@financehub.ru',
        full_name='Demo User',
        hashed_password=hash_password('demo123'),
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"✅ Пользователь создан!")
    print(f"   Email: {user.email}")
    print(f"   Password: demo123")
    print(f"   Active: {user.is_active}")
    print(f"   ID: {user.id}")

if __name__ == '__main__':
    main()

