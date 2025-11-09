"""Family budget and limits service."""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging

from app.models.family import (
    FamilyBudget,
    FamilyMemberLimit,
    FamilyBudgetPeriod,
    FamilyActivityLog,
    FamilyNotification,
    FamilyNotificationType,
    FamilyMember,
)
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.bank_connection import BankConnection
from app.schemas.family import (
    FamilyBudgetCreate,
    FamilyBudgetUpdate,
    FamilyMemberLimitCreate,
    FamilyMemberLimitUpdate,
)
from app.services.family_service import FamilyService
from fastapi import HTTPException, status


logger = logging.getLogger(__name__)


class FamilyBudgetService:
    """Service for managing family budgets and member limits."""
    
    @staticmethod
    def create_budget(
        db: Session,
        family_id: int,
        data: FamilyBudgetCreate,
        user_id: int
    ) -> FamilyBudget:
        """Create family budget."""
        if not FamilyService.is_admin(db, family_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create budgets"
            )
        
        budget = FamilyBudget(
            family_id=family_id,
            category_id=data.category_id,
            name=data.name,
            amount=data.amount,
            period=data.period,
            start_date=data.start_date,
            end_date=data.end_date,
            status="active"
        )
        db.add(budget)
        
        # Log activity
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=user_id,
            action="created_budget",
            target="family_budget",
            action_metadata={"budget_id": budget.id, "name": data.name, "amount": str(data.amount)}
        )
        db.add(log)
        
        db.commit()
        db.refresh(budget)
        return budget
    
    @staticmethod
    def get_family_budgets(db: Session, family_id: int) -> List[FamilyBudget]:
        """Get all family budgets."""
        FamilyBudgetService.evaluate_budget_notifications(db, family_id)

        return db.query(FamilyBudget).filter(
            FamilyBudget.family_id == family_id,
            FamilyBudget.status == "active"
        ).all()

    @staticmethod
    def evaluate_budget_notifications(db: Session, family_id: int) -> None:
        """Create notifications when budgets approach or exceed their limits."""
        budgets = db.query(FamilyBudget).filter(
            FamilyBudget.family_id == family_id,
            FamilyBudget.status == "active"
        ).all()

        if not budgets:
            return

        now = datetime.utcnow()
        notifications_created = False

        for budget in budgets:
            # Skip expired budgets
            if budget.end_date and budget.end_date < now:
                continue

            if not budget.amount or budget.amount <= 0:
                continue

            period_days = 7 if budget.period == FamilyBudgetPeriod.WEEKLY else 30
            period_start = now - timedelta(days=period_days)
            start_date = max(budget.start_date, period_start) if budget.start_date else period_start

            spent = FamilyBudgetService._calculate_budget_spending_for_period(db, family_id, budget, start_date)
            if spent <= 0:
                continue

            usage_ratio = float(spent / budget.amount) if budget.amount else 0

            thresholds = [
                (0.8, FamilyNotificationType.BUDGET_APPROACH),
                (1.0, FamilyNotificationType.BUDGET_EXCEEDED),
            ]

            for threshold_value, notification_type in thresholds:
                if usage_ratio >= threshold_value:
                    recent = FamilyBudgetService._find_recent_budget_notification(
                        db,
                        family_id,
                        budget.id,
                        notification_type
                    )

                    if recent:
                        continue

                    notification = FamilyNotification(
                        family_id=family_id,
                        member_id=None,
                        type=notification_type,
                        payload={
                            "budget_id": budget.id,
                            "budget_name": budget.name,
                            "budget_amount": str(budget.amount),
                            "spent": str(spent),
                            "percentage": round(usage_ratio * 100, 2),
                            "threshold": threshold_value,
                            "category_id": budget.category_id,
                            "period": budget.period.value,
                        },
                        status="new"
                    )
                    db.add(notification)
                    notifications_created = True
                    logger.info(
                        "📢 Budget notification created",
                        extra={
                            "family_id": family_id,
                            "budget_id": budget.id,
                            "type": notification_type.value,
                            "usage_ratio": usage_ratio,
                        }
                    )

        if notifications_created:
            db.commit()
    
    @staticmethod
    def update_budget(
        db: Session,
        budget_id: int,
        data: FamilyBudgetUpdate,
        user_id: int
    ) -> FamilyBudget:
        """Update family budget."""
        budget = db.query(FamilyBudget).filter(FamilyBudget.id == budget_id).first()
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found"
            )
        
        if not FamilyService.is_admin(db, budget.family_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update budgets"
            )
        
        if data.name:
            budget.name = data.name
        if data.amount:
            budget.amount = data.amount
        if data.period:
            budget.period = data.period
        if data.end_date:
            budget.end_date = data.end_date
        if data.status:
            budget.status = data.status
        
        db.commit()
        db.refresh(budget)
        return budget
 
    @staticmethod
    def _calculate_budget_spending_for_period(
        db: Session,
        family_id: int,
        budget: FamilyBudget,
        start_date: datetime
    ) -> Decimal:
        """Calculate spending for a specific budget within a period."""
        members = db.query(FamilyMember).filter(FamilyMember.family_id == family_id).all()
        if not members:
            return Decimal(0)

        user_ids = [m.user_id for m in members]

        query = db.query(func.sum(Transaction.amount)).join(
            Account, Transaction.account_id == Account.id
        ).join(
            BankConnection, Account.bank_connection_id == BankConnection.id
        ).filter(
            and_(
                BankConnection.user_id.in_(user_ids),
                Transaction.transaction_date >= start_date,
                Transaction.amount < 0
            )
        )

        if budget.category_id:
            query = query.filter(Transaction.category_id == budget.category_id)

        result = query.scalar()
        return abs(result) if result else Decimal(0)

    @staticmethod
    def create_member_limit(
        db: Session,
        family_id: int,
        data: FamilyMemberLimitCreate,
        user_id: int
    ) -> FamilyMemberLimit:
        """Create member spending limit."""
        if not FamilyService.is_admin(db, family_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can set limits"
            )
        
        limit = FamilyMemberLimit(
            family_id=family_id,
            member_id=data.member_id,
            category_id=data.category_id,
            amount=data.amount,
            period=data.period,
            auto_unlock=data.auto_unlock,
            status="active"
        )
        db.add(limit)
        
        # Log activity
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=user_id,
            action="set_limit",
            target="family_member_limit",
            action_metadata={"limit_id": limit.id, "member_id": data.member_id, "amount": str(data.amount)}
        )
        db.add(log)
        
        db.commit()
        db.refresh(limit)
        return limit
    
    @staticmethod
    def get_member_limits(db: Session, family_id: int, member_id: int) -> List[FamilyMemberLimit]:
        """Get all limits for a member."""
        return db.query(FamilyMemberLimit).filter(
            and_(
                FamilyMemberLimit.family_id == family_id,
                FamilyMemberLimit.member_id == member_id,
                FamilyMemberLimit.status == "active"
            )
        ).all()
    
    @staticmethod
    def check_limit_exceeded(
        db: Session,
        member_id: int,
        category_id: Optional[int],
        amount: Decimal
    ) -> tuple[bool, Optional[FamilyMemberLimit]]:
        """Check if transaction would exceed member's limit."""
        # Get active limits for member
        query = db.query(FamilyMemberLimit).filter(
            and_(
                FamilyMemberLimit.member_id == member_id,
                FamilyMemberLimit.status == "active"
            )
        )
        
        if category_id:
            query = query.filter(
                or_(
                    FamilyMemberLimit.category_id == category_id,
                    FamilyMemberLimit.category_id.is_(None)  # General limit
                )
            )
        else:
            query = query.filter(FamilyMemberLimit.category_id.is_(None))
        
        limits = query.all()
        
        for limit in limits:
            # Calculate current spending for the period
            current_spending = FamilyBudgetService._get_member_spending(
                db, member_id, limit.period, limit.category_id
            )
            
            if current_spending + amount > limit.amount:
                return True, limit
        
        return False, None
    
    @staticmethod
    def _get_member_spending(
        db: Session,
        member_id: int,
        period: FamilyBudgetPeriod,
        category_id: Optional[int] = None
    ) -> Decimal:
        """Calculate member's spending for the period."""
        from app.models.family import FamilyMember
        
        # Get member's user_id
        member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
        if not member:
            return Decimal(0)
        
        # Calculate period start date
        now = datetime.utcnow()
        if period == FamilyBudgetPeriod.WEEKLY:
            start_date = now - timedelta(days=7)
        else:  # MONTHLY
            start_date = now - timedelta(days=30)
        
        # Query transactions
        query = db.query(func.sum(Transaction.amount)).join(
            Account, Transaction.account_id == Account.id
        ).join(
            BankConnection, Account.bank_connection_id == BankConnection.id
        ).filter(
            and_(
                BankConnection.user_id == member.user_id,
                Transaction.transaction_date >= start_date,
                Transaction.amount < 0  # Only expenses
            )
        )
        
        if category_id:
            query = query.filter(Transaction.category_id == category_id)
        
        result = query.scalar()
        return abs(result) if result else Decimal(0)

    @staticmethod
    def _find_recent_budget_notification(
        db: Session,
        family_id: int,
        budget_id: int,
        notification_type: FamilyNotificationType,
        freshness_hours: int = 6
    ) -> Optional[FamilyNotification]:
        """Return last notification for this budget within freshness window."""
        recent_notifications = db.query(FamilyNotification).filter(
            FamilyNotification.family_id == family_id,
            FamilyNotification.type == notification_type
        ).order_by(FamilyNotification.created_at.desc()).limit(10).all()

        now = datetime.utcnow()
        for notification in recent_notifications:
            payload = notification.payload or {}
            if payload.get("budget_id") == budget_id:
                hours_passed = (now - notification.created_at).total_seconds() / 3600
                if hours_passed <= freshness_hours:
                    return notification

        return None

