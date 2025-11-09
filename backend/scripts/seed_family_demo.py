"""Seed script for Family Banking Hub demo data."""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.database import Base
from app.models.user import User
from app.models.family import (
    FamilyGroup,
    FamilyMember,
    FamilyMemberSettings,
    FamilyBudget,
    FamilyMemberLimit,
    FamilyGoal,
    FamilyGoalContribution,
    FamilyRole,
    FamilyMemberStatus,
    FamilyBudgetPeriod,
    FamilyGoalStatus,
)
from app.models.category import Category
from app.utils.security import hash_password


def create_family_demo_data(db: Session):
    """Create demo family data."""
    print("🏠 Creating Family Banking Hub demo data...")
    
    # Check if demo user exists
    demo_user = db.query(User).filter(User.email == "demo").first()
    if not demo_user:
        print("❌ Demo user not found. Please run create_demo_user.py first.")
        return
    
    # Create additional family members
    print("👥 Creating family members...")
    
    # Check if users already exist
    spouse = db.query(User).filter(User.email == "spouse@family.demo").first()
    if not spouse:
        spouse = User(
            email="spouse@family.demo",
            full_name="Анна Иванова",
            hashed_password=hash_password("demo123"),
            use_gost_mode=False
        )
        db.add(spouse)
        db.flush()
        print(f"  ✅ Created spouse user: {spouse.full_name}")
    
    child = db.query(User).filter(User.email == "child@family.demo").first()
    if not child:
        child = User(
            email="child@family.demo",
            full_name="Петя Иванов",
            hashed_password=hash_password("demo123"),
            use_gost_mode=False
        )
        db.add(child)
        db.flush()
        print(f"  ✅ Created child user: {child.full_name}")
    
    # Create family group
    print("\n🏠 Creating family group...")
    family = db.query(FamilyGroup).filter(FamilyGroup.name == "Семья Ивановых").first()
    if not family:
        family = FamilyGroup(
            name="Семья Ивановых",
            created_by=demo_user.id
        )
        db.add(family)
        db.flush()
        print(f"  ✅ Created family: {family.name}")
        print(f"  📋 Invite code: {family.invite_code}")
    else:
        print(f"  ℹ️  Family already exists: {family.name}")
    
    # Add family members
    print("\n👨‍👩‍👦 Adding family members...")
    
    # Admin (creator)
    admin_member = db.query(FamilyMember).filter(
        FamilyMember.family_id == family.id,
        FamilyMember.user_id == demo_user.id
    ).first()
    
    if not admin_member:
        admin_member = FamilyMember(
            family_id=family.id,
            user_id=demo_user.id,
            role=FamilyRole.ADMIN,
            status=FamilyMemberStatus.ACTIVE
        )
        db.add(admin_member)
        db.flush()
        
        # Create settings
        admin_settings = FamilyMemberSettings(
            member_id=admin_member.id,
            show_accounts=True,
            default_visibility="full"
        )
        db.add(admin_settings)
        print(f"  ✅ Added admin: {demo_user.full_name}")
    
    # Spouse
    spouse_member = db.query(FamilyMember).filter(
        FamilyMember.family_id == family.id,
        FamilyMember.user_id == spouse.id
    ).first()
    
    if not spouse_member:
        spouse_member = FamilyMember(
            family_id=family.id,
            user_id=spouse.id,
            role=FamilyRole.MEMBER,
            status=FamilyMemberStatus.ACTIVE
        )
        db.add(spouse_member)
        db.flush()
        
        spouse_settings = FamilyMemberSettings(
            member_id=spouse_member.id,
            show_accounts=True,
            default_visibility="full"
        )
        db.add(spouse_settings)
        print(f"  ✅ Added spouse: {spouse.full_name}")
    
    # Child
    child_member = db.query(FamilyMember).filter(
        FamilyMember.family_id == family.id,
        FamilyMember.user_id == child.id
    ).first()
    
    if not child_member:
        child_member = FamilyMember(
            family_id=family.id,
            user_id=child.id,
            role=FamilyRole.MEMBER,
            status=FamilyMemberStatus.ACTIVE
        )
        db.add(child_member)
        db.flush()
        
        child_settings = FamilyMemberSettings(
            member_id=child_member.id,
            show_accounts=True,
            default_visibility="limited"
        )
        db.add(child_settings)
        print(f"  ✅ Added child: {child.full_name}")
    
    # Get categories
    groceries_cat = db.query(Category).filter(Category.name == "Продукты").first()
    entertainment_cat = db.query(Category).filter(Category.name == "Развлечения").first()
    transport_cat = db.query(Category).filter(Category.name == "Транспорт").first()
    
    # Create family budgets
    print("\n💰 Creating family budgets...")
    
    budgets_data = [
        {
            "name": "Продукты питания",
            "category_id": groceries_cat.id if groceries_cat else None,
            "amount": Decimal("30000"),
            "period": FamilyBudgetPeriod.MONTHLY
        },
        {
            "name": "Развлечения",
            "category_id": entertainment_cat.id if entertainment_cat else None,
            "amount": Decimal("15000"),
            "period": FamilyBudgetPeriod.MONTHLY
        },
        {
            "name": "Транспорт",
            "category_id": transport_cat.id if transport_cat else None,
            "amount": Decimal("10000"),
            "period": FamilyBudgetPeriod.MONTHLY
        }
    ]
    
    for budget_data in budgets_data:
        existing = db.query(FamilyBudget).filter(
            FamilyBudget.family_id == family.id,
            FamilyBudget.name == budget_data["name"]
        ).first()
        
        if not existing:
            budget = FamilyBudget(
                family_id=family.id,
                **budget_data,
                start_date=datetime.utcnow(),
                status="active"
            )
            db.add(budget)
            print(f"  ✅ Created budget: {budget_data['name']} - {budget_data['amount']} ₽")
    
    # Create member limits (for child)
    print("\n🚦 Creating member limits...")
    
    limits_data = [
        {
            "member_id": child_member.id,
            "category_id": entertainment_cat.id if entertainment_cat else None,
            "amount": Decimal("5000"),
            "period": FamilyBudgetPeriod.MONTHLY,
            "auto_unlock": False
        },
        {
            "member_id": child_member.id,
            "category_id": None,  # General limit
            "amount": Decimal("10000"),
            "period": FamilyBudgetPeriod.MONTHLY,
            "auto_unlock": False
        }
    ]
    
    for limit_data in limits_data:
        existing = db.query(FamilyMemberLimit).filter(
            FamilyMemberLimit.family_id == family.id,
            FamilyMemberLimit.member_id == limit_data["member_id"],
            FamilyMemberLimit.category_id == limit_data["category_id"]
        ).first()
        
        if not existing:
            limit = FamilyMemberLimit(
                family_id=family.id,
                **limit_data,
                status="active"
            )
            db.add(limit)
            category_name = "Общий" if not limit_data["category_id"] else "Развлечения"
            print(f"  ✅ Created limit for {child.full_name}: {category_name} - {limit_data['amount']} ₽")
    
    # Create family goals
    print("\n🎯 Creating family goals...")
    
    goals_data = [
        {
            "name": "Отпуск в Сочи",
            "description": "Семейный отпуск на море летом 2025",
            "target_amount": Decimal("150000"),
            "deadline": datetime.utcnow() + timedelta(days=180)
        },
        {
            "name": "Новый телевизор",
            "description": "Samsung 65 дюймов для гостиной",
            "target_amount": Decimal("80000"),
            "deadline": datetime.utcnow() + timedelta(days=90)
        }
    ]
    
    for goal_data in goals_data:
        existing = db.query(FamilyGoal).filter(
            FamilyGoal.family_id == family.id,
            FamilyGoal.name == goal_data["name"]
        ).first()
        
        if not existing:
            goal = FamilyGoal(
                family_id=family.id,
                **goal_data,
                current_amount=Decimal("0"),
                status=FamilyGoalStatus.ACTIVE,
                created_by=demo_user.id
            )
            db.add(goal)
            db.flush()
            
            # Add initial contributions
            contributions = [
                {"member_id": admin_member.id, "amount": Decimal("20000")},
                {"member_id": spouse_member.id, "amount": Decimal("15000")},
                {"member_id": child_member.id, "amount": Decimal("5000")}
            ]
            
            for contrib_data in contributions:
                contribution = FamilyGoalContribution(
                    goal_id=goal.id,
                    **contrib_data
                )
                db.add(contribution)
                goal.current_amount += contrib_data["amount"]
            
            print(f"  ✅ Created goal: {goal_data['name']} - {goal_data['target_amount']} ₽")
            print(f"     💰 Initial contributions: {goal.current_amount} ₽")
    
    db.commit()
    print("\n✅ Family Banking Hub demo data created successfully!")
    print(f"\n📋 Family Invite Code: {family.invite_code}")
    print("\n👥 Demo Users:")
    print(f"  Admin: demo / demo123")
    print(f"  Spouse: spouse@family.demo / demo123")
    print(f"  Child: child@family.demo / demo123")


def main():
    """Main function."""
    print("=" * 60)
    print("Family Banking Hub - Demo Data Seeder")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        create_family_demo_data(db)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

