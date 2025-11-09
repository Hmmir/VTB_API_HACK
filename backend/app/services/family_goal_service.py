"""Family goals service."""
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.integrations.mybank_client import MyBankClient, DEFAULT_MYBANK_PASSWORD
from app.models.account import Account, AccountType
from app.models.family import (
    FamilyGoal,
    FamilyGoalContribution,
    FamilyGoalStatus,
    FamilyActivityLog,
)
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.family import (
    FamilyGoalCreate,
    FamilyGoalUpdate,
    FamilyGoalContributionCreate,
)
from app.services.family_service import FamilyService


logger = logging.getLogger(__name__)


class FamilyGoalService:
    """Service for managing family goals."""
    
    @staticmethod
    async def create_goal(
        db: Session,
        family_id: int,
        data: FamilyGoalCreate,
        user_id: int
    ) -> FamilyGoal:
        """Create family goal with MyBank account."""
        if not FamilyService.is_member(db, family_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only family members can create goals"
            )
        
        # Создаем цель в БД
        goal = FamilyGoal(
            family_id=family_id,
            name=data.name,
            description=data.description,
            target_amount=data.target_amount,
            current_amount=Decimal(0),
            deadline=data.deadline,
            status=FamilyGoalStatus.ACTIVE,
            created_by=user_id
        )
        db.add(goal)
        db.flush()  # Получаем ID цели
        
        # Создаем MyBank счет для цели
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        mybank = MyBankClient()
        
        # Login or register in MyBank
        try:
            await mybank.login(user.email, DEFAULT_MYBANK_PASSWORD)
        except Exception as login_err:
            logger.info(f"Login failed, trying to register: {login_err}")
            try:
                await mybank.register_customer(
                    full_name=user.full_name or user.email.split('@')[0],
                    email=user.email,
                    phone=user.phone or "+70000000000",
                    password=DEFAULT_MYBANK_PASSWORD
                )
            except Exception as reg_err:
                # 400 = уже зарегистрирован, это нормально
                logger.info(f"Registration failed (may already exist): {reg_err}")
            
            try:
                await mybank.login(user.email, DEFAULT_MYBANK_PASSWORD)
            except Exception as login_err2:
                logger.error(f"MyBank login failed after registration: {login_err2}")
                # Продолжаем без MyBank счета
        
        # Create goal in MyBank
        try:
            mybank_goal = await mybank.create_goal(
                name=data.name,
                target_amount=data.target_amount,
                deadline=data.deadline
            )
            
            logger.info(f"✅ MyBank goal created: {mybank_goal}")
            
            # Создаем Account в FinanceHub для MyBank счета цели
            family_goal_account = Account(
                bank_connection_id=None,
                account_name=f"Family Goal: {data.name}",
                account_number=mybank_goal.get('account_number', mybank_goal['account_id']),
                account_type=AccountType.SAVINGS,
                balance=Decimal("0"),
                currency="RUB",
                is_active=1,
                external_account_id=mybank_goal['account_id'],
                family_id=family_id,
            )
            db.add(family_goal_account)
            db.flush()
            
            # Добавляем счет в семейные счета
            from app.models.family import FamilySharedAccount, FamilyMember
            
            # Находим создателя как члена семьи
            creator_member = db.query(FamilyMember).filter(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == user_id
            ).first()
            
            if creator_member:
                shared_account = FamilySharedAccount(
                    family_id=family_id,
                    member_id=creator_member.id,
                    account_id=family_goal_account.id
                )
                db.add(shared_account)
                db.flush()  # Важно: сохраняем связь сразу
                logger.info(f"✅ Family goal account added to shared accounts: account_id={family_goal_account.id}, member_id={creator_member.id}")
            else:
                logger.error(f"❌ Creator member not found for user_id={user_id}, family_id={family_id}")
            
            # Сохраняем MyBank goal_id в metadata цели
            goal.metadata = {
                "mybank_goal_id": mybank_goal['goal_id'],
                "mybank_account_id": family_goal_account.id,
                "mybank_account_external_id": mybank_goal['account_id'],
            }
            
        except Exception as mybank_err:
            logger.error(f"⚠️ Failed to create MyBank goal: {mybank_err}")
            # Продолжаем без MyBank счета, но добавляем уведомление в metadata
            goal.metadata = {"mybank_error": str(mybank_err), "needs_mybank_account": True}
        
        # Log activity
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=user_id,
            action="created_goal",
            target="family_goal",
            action_metadata={"goal_id": goal.id, "name": data.name, "target": str(data.target_amount)}
        )
        db.add(log)
        
        db.commit()
        db.refresh(goal)
        return goal
    
    @staticmethod
    def get_family_goals(db: Session, family_id: int) -> List[FamilyGoal]:
        """Get all family goals."""
        return db.query(FamilyGoal).filter(
            FamilyGoal.family_id == family_id
        ).all()
    
    @staticmethod
    async def contribute_to_goal(
        db: Session,
        goal_id: int,
        member_id: int,
        data: FamilyGoalContributionCreate,
        user_id: int
    ) -> FamilyGoalContribution:
        """Make contribution to goal."""
        goal = db.query(FamilyGoal).filter(FamilyGoal.id == goal_id).first()
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )

        if goal.status != FamilyGoalStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Goal is not active"
            )

        source_account = db.query(Account).filter(Account.id == data.source_account_id).first()
        if not source_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source account not found"
            )

        if source_account.balance < data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient funds. Balance: {source_account.balance} ₽"
            )

        # Ищем MyBank счет семейной цели по имени
        import logging
        logger = logging.getLogger(__name__)
        
        mybank_account = db.query(Account).filter(
            Account.family_id == goal.family_id,
            Account.bank_connection_id.is_(None),
            Account.account_name == f"Family Goal: {goal.name}"
        ).first()
        
        logger.info(f"💰 Contributing to goal '{goal.name}': amount={data.amount}, source_account={data.source_account_id}")
        logger.info(f"💰 MyBank account for goal: {mybank_account.id if mybank_account else 'NOT FOUND'}")

        # Добавляем взнос и обновляем цель
        contribution = FamilyGoalContribution(
            goal_id=goal_id,
            member_id=member_id,
            amount=data.amount,
            source_account_id=data.source_account_id
        )
        db.add(contribution)

        goal.current_amount += data.amount
        if goal.current_amount >= goal.target_amount:
            goal.status = FamilyGoalStatus.COMPLETED
            goal.completed_at = datetime.utcnow()

        # Списываем деньги со счета-источника
        source_account.balance -= data.amount
        db.add(source_account)

        expense_tx_id = f"FAMILY_GOAL_CONTRIB_{goal_id}_{uuid.uuid4().hex}"
        expense_tx = Transaction(
            account_id=data.source_account_id,
            external_transaction_id=expense_tx_id,
            amount=-data.amount,
            description=f"Взнос на семейную цель: {goal.name}",
            transaction_date=datetime.utcnow(),
            transaction_type=TransactionType.EXPENSE,
            category_id=None
        )
        db.add(expense_tx)
        logger.info(f"✅ Created EXPENSE transaction: account_id={data.source_account_id}, amount=-{data.amount}")

        # Зачисляем на MyBank счет цели в FinanceHub
        if mybank_account:
            mybank_account.balance += data.amount
            db.add(mybank_account)

            income_tx_id = f"FAMILY_GOAL_DEPOSIT_{goal_id}_{uuid.uuid4().hex}"
            income_tx = Transaction(
                account_id=mybank_account.id,
                external_transaction_id=income_tx_id,
                amount=data.amount,
                description=f"Взнос на семейную цель: {goal.name}",
                transaction_date=datetime.utcnow(),
                transaction_type=TransactionType.INCOME,
                category_id=None
            )
            db.add(income_tx)
            logger.info(f"✅ Created INCOME transaction: account_id={mybank_account.id}, amount=+{data.amount}")
        else:
            logger.warning(f"⚠️ MyBank account not found for goal '{goal.name}', INCOME transaction not created")

        # Log activity
        log = FamilyActivityLog(
            family_id=goal.family_id,
            actor_id=user_id,
            action="contributed_to_goal",
            target="family_goal",
            action_metadata={"goal_id": goal_id, "amount": str(data.amount)}
        )
        db.add(log)

        db.commit()
        db.refresh(contribution)
        return contribution

