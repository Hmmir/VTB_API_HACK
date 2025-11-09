"""
Seed Demo Data for Hackathon Presentation
Creates realistic family banking scenario
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.user import User
from app.models.category import Category
from app.models.family import (
    FamilyGroup, FamilyMember, FamilyBudget, FamilyGoal,
    FamilyRole, FamilyMemberStatus, FamilyBudgetPeriod, FamilyGoalStatus
)
from app.utils.security import hash_password
from decimal import Decimal
from datetime import datetime, timedelta
import secrets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_demo_users(db: Session):
    """Create demo family members"""
    users_data = [
        {
            "email": "anna@family.ru",
            "full_name": "Анна Иванова",
            "password": "demo123",
            "phone": "+79001234567"
        },
        {
            "email": "sergey@family.ru",
            "full_name": "Сергей Иванов",
            "password": "demo123",
            "phone": "+79001234568"
        },
        {
            "email": "maria@family.ru",
            "full_name": "Мария Иванова",
            "password": "demo123",
            "phone": "+79001234569"
        }
    ]
    
    users = []
    for data in users_data:
        existing = db.query(User).filter(User.email == data["email"]).first()
        if existing:
            users.append(existing)
            logger.info(f"User {data['email']} already exists")
            continue
            
        user = User(
            email=data["email"],
            full_name=data["full_name"],
            hashed_password=hash_password(data["password"]),
            phone=data["phone"],
            is_active=True
        )
        db.add(user)
        db.flush()
        users.append(user)
        logger.info(f"Created user: {data['email']}")
    
    db.commit()
    return users


def create_categories(db: Session):
    """Create expense categories"""
    categories_data = [
        {"name": "Продукты", "icon": "🛒", "color": "#4CAF50"},
        {"name": "Развлечения", "icon": "🎮", "color": "#2196F3"},
        {"name": "Образование", "icon": "📚", "color": "#FF9800"},
        {"name": "Транспорт", "icon": "🚗", "color": "#9C27B0"},
        {"name": "Здоровье", "icon": "🏥", "color": "#F44336"},
        {"name": "Коммунальные услуги", "icon": "💡", "color": "#607D8B"}
    ]
    
    categories = []
    for data in categories_data:
        existing = db.query(Category).filter(Category.name == data["name"]).first()
        if existing:
            categories.append(existing)
            continue
            
        category = Category(**data)
            db.add(category)
        db.flush()
        categories.append(category)
        logger.info(f"Created category: {data['name']}")
    
    db.commit()
    return categories


def create_family_group(db: Session, admin_user: User):
    """Create demo family group"""
    invite_code = secrets.token_urlsafe(8)
    
    family = FamilyGroup(
        name="Семья Ивановых",
        created_by=admin_user.id,
        invite_code=invite_code
    )
    db.add(family)
    db.flush()
    logger.info(f"Created family group: {family.name} (invite: {invite_code})")
    
    return family


def add_family_members(db: Session, family: FamilyGroup, users: list):
    """Add users to family"""
    members = []
    
    # First user is admin
    admin_member = FamilyMember(
        family_id=family.id,
        user_id=users[0].id,
        role=FamilyRole.ADMIN,
        status=FamilyMemberStatus.ACTIVE
    )
    db.add(admin_member)
    db.flush()
    members.append(admin_member)
    logger.info(f"Added admin: {users[0].full_name}")
    
    # Others are regular members
    for user in users[1:]:
        member = FamilyMember(
            family_id=family.id,
            user_id=user.id,
            role=FamilyRole.MEMBER,
            status=FamilyMemberStatus.ACTIVE
        )
        db.add(member)
        db.flush()
        members.append(member)
        logger.info(f"Added member: {user.full_name}")
    
    db.commit()
    return members


def create_family_budgets(db: Session, family: FamilyGroup, categories: list):
    """Create family budgets"""
    budgets_data = [
        {
            "name": "Продукты на месяц",
            "category_id": categories[0].id,
            "amount": Decimal("50000.00"),
            "period": FamilyBudgetPeriod.MONTHLY
        },
        {
            "name": "Развлечения",
            "category_id": categories[1].id,
            "amount": Decimal("15000.00"),
            "period": FamilyBudgetPeriod.MONTHLY
        },
        {
            "name": "Образование детей",
            "category_id": categories[2].id,
            "amount": Decimal("30000.00"),
            "period": FamilyBudgetPeriod.MONTHLY
        }
    ]
    
    budgets = []
    start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    
    for data in budgets_data:
        budget = FamilyBudget(
            family_id=family.id,
            **data,
            start_date=start_date,
            end_date=end_date,
            status="active"
        )
        db.add(budget)
        db.flush()
        budgets.append(budget)
        logger.info(f"Created budget: {data['name']}")
    
    db.commit()
    return budgets


def create_family_goals(db: Session, family: FamilyGroup, admin_user: User):
    """Create family goals"""
    goals_data = [
        {
            "name": "Отпуск в Сочи",
            "description": "Семейный отпуск летом 2026",
            "target_amount": Decimal("200000.00"),
            "deadline": datetime(2026, 6, 1)
        },
        {
            "name": "Ремонт квартиры",
            "description": "Ремонт детской комнаты",
            "target_amount": Decimal("150000.00"),
            "deadline": datetime(2026, 3, 1)
        },
        {
            "name": "Новый автомобиль",
            "description": "Накопления на семейный автомобиль",
            "target_amount": Decimal("800000.00"),
            "deadline": datetime(2027, 1, 1)
        }
    ]
    
    goals = []
    for data in goals_data:
        goal = FamilyGoal(
            family_id=family.id,
            created_by=admin_user.id,
            status=FamilyGoalStatus.ACTIVE,
            current_amount=Decimal("0.00"),
            **data
        )
        db.add(goal)
        db.flush()
        goals.append(goal)
        logger.info(f"Created goal: {data['name']}")
    
    db.commit()
    return goals


def main():
    """Main seed function - только базовые данные, семью создает сам пользователь"""
    logger.info("=" * 60)
    logger.info("SEEDING BASIC DATA (Categories only)")
    logger.info("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Create categories
        logger.info("\n[1/1] Creating categories...")
        categories = create_categories(db)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ BASIC DATA SEEDED!")
        logger.info("=" * 60)
        logger.info(f"\n📊 Summary:")
        logger.info(f"   • Categories: {len(categories)}")
        logger.info(f"\n💡 Пользователь САМ создаст:")
        logger.info(f"   • Семейную группу")
        logger.info(f"   • Цели (автоматически создастся счет в MyBank)")
        logger.info(f"   • Семейные счета")
        
    except Exception as e:
        logger.error(f"❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
