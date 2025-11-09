"""Analytics endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.models.account import Account
from app.models.category import Category
from app.services.ai_insights import AIInsightsService

router = APIRouter()


@router.get("/summary")
def get_analytics_summary(
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get financial analytics summary for the specified period."""
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get user's accounts
    account_ids = [acc.id for acc in db.query(Account).join(Account.bank_connection).filter(
        Account.bank_connection.has(user_id=current_user.id)
    ).all()]
    
    if not account_ids:
        return {
            "total_income": 0,
            "total_expenses": 0,
            "net_balance": 0,
            "period_days": period_days,
            "transaction_count": 0
        }
    
    # Calculate totals
    income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).scalar() or 0
    
    expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).scalar() or 0
    
    tx_count = db.query(func.count(Transaction.id)).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).scalar() or 0
    
    return {
        "total_income": float(income),
        "total_expenses": float(expenses),
        "net_balance": float(income - expenses),
        "period_days": period_days,
        "transaction_count": int(tx_count),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }


@router.get("/by-category")
def get_expenses_by_category(
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get expenses grouped by category."""
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get user's accounts
    account_ids = [acc.id for acc in db.query(Account).join(Account.bank_connection).filter(
        Account.bank_connection.has(user_id=current_user.id)
    ).all()]
    
    if not account_ids:
        return []
    
    # Query expenses by category
    results = db.query(
        Category.name,
        Category.id,
        func.sum(Transaction.amount).label("total"),
        func.count(Transaction.id).label("count")
    ).join(
        Transaction, Transaction.category_id == Category.id
    ).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).group_by(
        Category.id, Category.name
    ).order_by(
        func.sum(Transaction.amount).desc()
    ).all()
    
    return [
        {
            "category": row.name,
            "category_id": row.id,
            "total": float(row.total),
            "count": int(row.count)
        }
        for row in results
    ]


@router.get("/trends")
def get_spending_trends(
    period_days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get daily spending trends."""
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get user's accounts
    account_ids = [acc.id for acc in db.query(Account).join(Account.bank_connection).filter(
        Account.bank_connection.has(user_id=current_user.id)
    ).all()]
    
    if not account_ids:
        return []
    
    # Query daily expenses
    from sqlalchemy import case
    results = db.query(
        func.date(Transaction.transaction_date).label("date"),
        func.sum(
            case(
                (Transaction.transaction_type == TransactionType.EXPENSE, Transaction.amount),
                else_=0
            )
        ).label("expenses"),
        func.sum(
            case(
                (Transaction.transaction_type == TransactionType.INCOME, Transaction.amount),
                else_=0
            )
        ).label("income")
    ).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).group_by(
        func.date(Transaction.transaction_date)
    ).order_by(
        func.date(Transaction.transaction_date)
    ).all()
    
    return [
        {
            "date": row.date.isoformat(),
            "expenses": float(row.expenses),
            "income": float(row.income),
            "net": float(row.income - row.expenses)
        }
        for row in results
    ]


@router.get("/ai-insights")
def get_ai_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get AI-powered budget insights and recommendations.
    
    Analyzes user's transaction history and generates:
    - Top spending categories
    - Spending trends
    - Savings potential
    - Unusual activity detection
    - Optimization tips
    """
    insights = AIInsightsService.generate_insights(db, current_user.id)
    
    return {
        "insights": insights,
        "count": len(insights),
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/financial-health")
def get_financial_health_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get financial health score (0-100) based on:
    - Savings rate (40%)
    - Expense stability (30%)
    - Account balances (30%)
    
    Returns score, grade (A+, A, B, C, D), and detailed breakdown.
    """
    health = AIInsightsService.get_financial_health_score(db, current_user.id)
    
    return {
        "health": health,
        "calculated_at": datetime.utcnow().isoformat()
    }

