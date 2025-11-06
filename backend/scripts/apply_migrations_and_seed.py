"""Apply migrations and seed database with demo data."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import *  # Import all models
from app.utils.security import hash_password


def drop_all_tables():
    """Drop all tables (for clean start)."""
    print("🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")


def create_all_tables():
    """Create all tables from models."""
    print("📋 Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created")


def seed_demo_data(db: Session):
    """Seed database with demo data."""
    print("\n🌱 Seeding demo data...")
    
    # 1. Create demo users
    print("  👤 Creating demo users...")
    user1 = User(
        email="demo@example.com",
        hashed_password=hash_password("demo123"),
        full_name="Демо Пользователь",
        phone="+79001234567"
    )
    user2 = User(
        email="ivan@example.com",
        hashed_password=hash_password("password123"),
        full_name="Иван Петров",
        phone="+79009876543"
    )
    db.add_all([user1, user2])
    db.flush()
    
    # 2. Create partner banks
    print("  🏦 Creating partner banks...")
    vtb = PartnerBank(
        id=str(uuid4()),
        code="VTB",
        name="ВТБ Банк",
        api_endpoint="https://api.vtb.ru",
        jwks_uri="https://api.vtb.ru/.well-known/jwks.json"
    )
    sber = PartnerBank(
        id=str(uuid4()),
        code="SBER",
        name="Сбербанк",
        api_endpoint="https://api.sber.ru",
        jwks_uri="https://api.sber.ru/.well-known/jwks.json"
    )
    alpha = PartnerBank(
        id=str(uuid4()),
        code="ALPHA",
        name="Альфа-Банк",
        api_endpoint="https://api.alfabank.ru",
        jwks_uri="https://api.alfabank.ru/.well-known/jwks.json"
    )
    db.add_all([vtb, sber, alpha])
    db.flush()
    
    # 3. Skip BankConnection/Accounts for now (complex structure)
    # Users can connect banks via UI
    print("  ⏭️  Skipping bank connections (users will connect via UI)")
    
    # 3a. Create Family Hub demo data
    print("  👨‍👩‍👧 Creating family hub demo...")
    family_group = FamilyGroup(
        name="Семья Демидовых",
        description="Демонстрационная семейная группа",
        created_by_user_id=user1.id,
        invite_code="DEMOTEAM",
    )
    db.add(family_group)
    db.flush()

    family_admin = FamilyMember(
        family_id=family_group.id,
        user_id=user1.id,
        role=FamilyRole.ADMIN,
        status=FamilyMemberStatus.ACTIVE,
        joined_at=datetime.utcnow(),
    )
    family_member = FamilyMember(
        family_id=family_group.id,
        user_id=user2.id,
        role=FamilyRole.MEMBER,
        status=FamilyMemberStatus.ACTIVE,
        joined_at=datetime.utcnow(),
    )
    db.add_all([family_admin, family_member])
    db.flush()

    admin_settings = FamilyMemberSettings(member_id=family_admin.id, show_accounts=True, default_visibility="family")
    member_settings = FamilyMemberSettings(member_id=family_member.id, show_accounts=True, default_visibility="family")
    db.add_all([admin_settings, member_settings])

    demo_budget = FamilyBudget(
        family_id=family_group.id,
        name="Домашние расходы",
        amount=Decimal("75000.00"),
        period=FamilyBudgetPeriod.MONTHLY,
        status=FamilyBudgetStatus.ACTIVE,
        created_by_member_id=family_admin.id,
    )
    demo_limit = FamilyMemberLimit(
        family_id=family_group.id,
        member_id=family_member.id,
        amount=Decimal("15000.00"),
        period=FamilyMemberLimitPeriod.MONTHLY,
        status=FamilyMemberLimitStatus.ACTIVE,
        auto_unlock=False,
    )
    demo_goal = FamilyGoal(
        family_id=family_group.id,
        name="Поездка к морю",
        description="Совместная цель для отпуска",
        target_amount=Decimal("200000.00"),
        current_amount=Decimal("45000.00"),
        status=FamilyGoalStatus.ACTIVE,
        created_by_member_id=family_admin.id,
    )
    db.add_all([demo_budget, demo_limit, demo_goal])

    # 6. Create bank products
    print("  📦 Creating bank products...")
    from app.models.bank_product import ProductType as BPProductType
    products = [
        BankProduct(
            bank_provider="VTB",
            name="Накопительный счет 'Сбережения'",
            product_type=BPProductType.DEPOSIT,
            interest_rate=Decimal("7.5"),
            description="Высокий процент на остаток",
            min_amount=Decimal("10000.00")
        ),
        BankProduct(
            bank_provider="VTB",
            name="Потребительский кредит",
            product_type=BPProductType.LOAN,
            interest_rate=Decimal("12.9"),
            description="Кредит наличными на любые цели",
            min_amount=Decimal("50000.00")
        ),
        BankProduct(
            bank_provider="SBER",
            name="Кредитная карта 'Золотая'",
            product_type=BPProductType.CREDIT_CARD,
            interest_rate=Decimal("19.9"),
            description="Кредитная карта с кэшбэком",
            min_amount=Decimal("0.00")
        ),
    ]
    db.add_all(products)
    db.flush()
    
    # 7. Create consent (via ConsentRequest -> Consent)
    print("  ✅ Creating consents...")
    consent_request1 = ConsentRequest(
        id=str(uuid4()),
        user_id=user1.id,
        partner_bank_id=alpha.id,
        scopes=[ConsentScope.ACCOUNTS_READ.value, ConsentScope.TRANSACTIONS_READ.value, ConsentScope.PAYMENTS_WRITE.value],
        purpose="Демо согласие для межбанковских переводов",
        status=ConsentStatus.APPROVED,
        valid_from=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=90),
        requested_at=datetime.utcnow(),
        decided_at=datetime.utcnow()
    )
    db.add(consent_request1)
    db.flush()
    
    consent1 = Consent(
        id=str(uuid4()),
        request_id=consent_request1.id,
        user_id=user1.id,
        partner_bank_id=alpha.id,
        scopes=[ConsentScope.ACCOUNTS_READ.value, ConsentScope.TRANSACTIONS_READ.value, ConsentScope.PAYMENTS_WRITE.value],
        status=ConsentStatus.ACTIVE,
        valid_from=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=90)
    )
    db.add(consent1)
    
    # 8. Skip product agreements for now (enum mismatch issue)
    print("  ⏭️  Skipping product agreements (users can create via UI)")
    agreement1 = None
    
    # 9. Create notifications (simplified)
    print("  🔔 Creating notifications...")
    notif1 = Notification(
        id=str(uuid4()),
        user_id=user1.id,
        type=NotificationType.GOAL_ACHIEVED,
        priority=NotificationPriority.MEDIUM,
        title="🎉 Добро пожаловать!",
        message="Ваш аккаунт успешно создан. Подключите банки для начала работы.",
        is_read=False
    )
    notif2 = Notification(
        id=str(uuid4()),
        user_id=user1.id,
        type=NotificationType.SYSTEM,
        priority=NotificationPriority.LOW,
        title="Новые функции доступны",
        message="Теперь вы можете создавать межбанковские переводы и управлять согласиями",
        is_read=False
    )
    db.add_all([notif1, notif2])
    
    # 10. Skip budgets and goals (users can create via UI)
    print("  ⏭️  Skipping budgets and goals (users can create via UI)")
    
    db.commit()
    print("✅ Demo data seeded successfully!")
    print(f"  👤 Users: {db.query(User).count()}")
    print(f"  🏦 Partner Banks: {db.query(PartnerBank).count()}")
    print(f"  📦 Bank Products: {db.query(BankProduct).count()}")
    print(f"  ✅ Consent Requests: {db.query(ConsentRequest).count()}")
    print(f"  ✅ Consents: {db.query(Consent).count()}")
    print(f"  🔔 Notifications: {db.query(Notification).count()}")


def main():
    """Main function."""
    print("=" * 60)
    print("🚀 DATABASE SETUP & MIGRATION")
    print("=" * 60)
    
    # Step 1: Drop all tables
    drop_all_tables()
    
    # Step 2: Create all tables
    create_all_tables()
    
    # Step 3: Seed demo data
    db = SessionLocal()
    try:
        seed_demo_data(db)
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    print("\n📌 Demo credentials:")
    print("  Email: demo@example.com")
    print("  Password: demo123")
    print("\n🌐 API Documentation:")
    print("  http://localhost:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    main()

