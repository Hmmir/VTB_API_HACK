"""Family analytics service."""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.models.family import FamilyMember, FamilyBudget, FamilyMemberLimit, FamilyGoal
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.bank_connection import BankConnection
from app.models.category import Category


class FamilyAnalyticsService:
    """Service for family analytics."""
    
    @staticmethod
    def get_family_summary(
        db: Session,
        family_id: int,
        period_days: int = 30
    ) -> Dict:
        """Get family financial summary."""
        start_date = datetime.utcnow() - timedelta(days=period_days)

        # Evaluate budgets to trigger threshold notifications before returning analytics
        from app.services.family_budget_service import FamilyBudgetService
        FamilyBudgetService.evaluate_budget_notifications(db, family_id)
        
        # Get all family members
        members = db.query(FamilyMember).filter(
            FamilyMember.family_id == family_id
        ).all()
        
        user_ids = [m.user_id for m in members]
        
        # Get family shared account IDs
        from app.models.family import FamilySharedAccount
        shared_accounts = db.query(FamilySharedAccount).filter(
            FamilySharedAccount.family_id == family_id
        ).all()
        family_account_ids = [sa.account_id for sa in shared_accounts]
        
        # Calculate total income and expenses from family shared accounts only
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"📊 Family Analytics: family_id={family_id}, family_account_ids={family_account_ids}")
        
        if not family_account_ids:
            logger.warning(f"⚠️ No family shared accounts for family {family_id}")
            transactions = []
        else:
            transactions = db.query(Transaction).join(
                Account, Transaction.account_id == Account.id
            ).filter(
                and_(
                    Transaction.account_id.in_(family_account_ids),
                    Transaction.transaction_date >= start_date
                )
            ).all()
            logger.info(f"📊 Found {len(transactions)} transactions for family accounts")
        
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        total_expenses = abs(sum(t.amount for t in transactions if t.amount < 0))
        net_balance = total_income - total_expenses
        
        logger.info(f"📊 Analytics results: income={total_income}, expenses={total_expenses}, balance={net_balance}")
        
        # Budget usage
        budgets = db.query(FamilyBudget).filter(
            FamilyBudget.family_id == family_id,
            FamilyBudget.status == "active"
        ).all()
        
        budget_usage = []
        for budget in budgets:
            spent = FamilyAnalyticsService._calculate_budget_spending(
                db, family_id, budget, start_date
            )
            budget_usage.append({
                "budget_id": budget.id,
                "name": budget.name,
                "amount": float(budget.amount),
                "spent": float(spent),
                "percentage": float((spent / budget.amount) * 100) if budget.amount > 0 else 0
            })
        
        # Limit usage
        limits = db.query(FamilyMemberLimit).filter(
            FamilyMemberLimit.family_id == family_id,
            FamilyMemberLimit.status == "active"
        ).all()
        
        limit_usage = []
        for limit in limits:
            spent = FamilyAnalyticsService._calculate_member_spending(
                db, limit.member_id, start_date, limit.category_id
            )
            limit_usage.append({
                "limit_id": limit.id,
                "member_id": limit.member_id,
                "amount": float(limit.amount),
                "spent": float(spent),
                "percentage": float((spent / limit.amount) * 100) if limit.amount > 0 else 0
            })
        
        # Goal progress
        goals = db.query(FamilyGoal).filter(
            FamilyGoal.family_id == family_id
        ).all()
        
        goal_progress = []
        for goal in goals:
            goal_progress.append({
                "goal_id": goal.id,
                "name": goal.name,
                "target": float(goal.target_amount),
                "current": float(goal.current_amount),
                "percentage": float((goal.current_amount / goal.target_amount) * 100) if goal.target_amount > 0 else 0,
                "status": goal.status.value
            })
        
        # Top categories (from family shared accounts only)
        if not family_account_ids:
            category_spending = []
        else:
            category_spending = db.query(
                Category.name,
                func.sum(Transaction.amount).label('total')
            ).join(
                Transaction, Category.id == Transaction.category_id
            ).filter(
                and_(
                    Transaction.account_id.in_(family_account_ids),
                    Transaction.transaction_date >= start_date,
                    Transaction.amount < 0
                )
            ).group_by(Category.name).order_by(func.sum(Transaction.amount)).limit(5).all()
        
        top_categories = [
            {"category": cat.name, "amount": float(abs(cat.total))}
            for cat in category_spending
        ]
        
        # Member spending
        member_spending = []
        for member in members:
            spent = FamilyAnalyticsService._calculate_member_spending(
                db, member.id, start_date
            )
            member_spending.append({
                "member_id": member.id,
                "user_id": member.user_id,
                "spent": float(spent)
            })
        
        return {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_balance": float(net_balance),
            "budget_usage": budget_usage,
            "limit_usage": limit_usage,
            "goal_progress": goal_progress,
            "top_categories": top_categories,
            "member_spending": member_spending
        }
    
    @staticmethod
    def _calculate_budget_spending(
        db: Session,
        family_id: int,
        budget: FamilyBudget,
        start_date: datetime
    ) -> Decimal:
        """Calculate spending for a budget."""
        members = db.query(FamilyMember).filter(
            FamilyMember.family_id == family_id
        ).all()
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
    def _calculate_member_spending(
        db: Session,
        member_id: int,
        start_date: datetime,
        category_id: Optional[int] = None
    ) -> Decimal:
        """Calculate member spending."""
        member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
        if not member:
            return Decimal(0)
        
        query = db.query(func.sum(Transaction.amount)).join(
            Account, Transaction.account_id == Account.id
        ).join(
            BankConnection, Account.bank_connection_id == BankConnection.id
        ).filter(
            and_(
                BankConnection.user_id == member.user_id,
                Transaction.transaction_date >= start_date,
                Transaction.amount < 0
            )
        )
        
        if category_id:
            query = query.filter(Transaction.category_id == category_id)
        
        result = query.scalar()
        return abs(result) if result else Decimal(0)

