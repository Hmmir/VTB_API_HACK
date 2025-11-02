"""Seed script for demo data."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, engine, Base
from app.models import Category
from app.utils.security import hash_password
from datetime import datetime

def seed_categories(db):
    """Seed default categories."""
    categories = [
        {"name": "Продукты", "icon": "🛒", "color": "#10B981", "is_system": 1},
        {"name": "Транспорт", "icon": "🚗", "color": "#3B82F6", "is_system": 1},
        {"name": "Развлечения", "icon": "🎬", "color": "#8B5CF6", "is_system": 1},
        {"name": "Здоровье", "icon": "⚕️", "color": "#EF4444", "is_system": 1},
        {"name": "Образование", "icon": "📚", "color": "#F59E0B", "is_system": 1},
        {"name": "Коммунальные услуги", "icon": "🏠", "color": "#6366F1", "is_system": 1},
        {"name": "Одежда", "icon": "👕", "color": "#EC4899", "is_system": 1},
        {"name": "Подписки", "icon": "📱", "color": "#14B8A6", "is_system": 1},
        {"name": "Зарплата", "icon": "💰", "color": "#10B981", "is_system": 1},
        {"name": "Другое", "icon": "📦", "color": "#6B7280", "is_system": 1},
    ]
    
    for cat_data in categories:
        existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if not existing:
            category = Category(**cat_data)
            db.add(category)
    
    db.commit()
    print(f"✓ Seeded {len(categories)} categories")


def main():
    """Run all seed functions."""
    print("Starting database seed...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        seed_categories(db)
        print("\n✅ Database seeding completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

