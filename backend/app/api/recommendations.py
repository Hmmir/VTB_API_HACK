"""Recommendations endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.models.account import Account
from sqlalchemy import func

router = APIRouter()


@router.get("/")
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get personalized financial recommendations."""
    
    recommendations = []
    
    # Get user's accounts
    account_ids = [acc.id for acc in db.query(Account).join(Account.bank_connection).filter(
        Account.bank_connection.has(user_id=current_user.id)
    ).all()]
    
    if not account_ids:
        return []
    
    # Calculate total balance
    total_balance = db.query(func.sum(Account.balance)).filter(
        Account.id.in_(account_ids)
    ).scalar() or 0
    
    # Calculate monthly income and expenses (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.transaction_date >= start_date
    ).scalar() or 0
    
    expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start_date
    ).scalar() or 0
    
    net_savings = income - expenses
    
    # Recommendation 1: Deposit for large positive balance
    if total_balance > 50000:
        recommendations.append({
            "id": "deposit-recommendation",
            "type": "deposit",
            "priority": "high",
            "title": "💰 Откройте депозит и получайте проценты",
            "description": f"У вас на счетах {total_balance:,.0f} ₽. Разместив деньги на депозите под 8% годовых, вы будете получать ~{total_balance * 0.08 / 12:,.0f} ₽ в месяц.",
            "action": "Открыть депозит",
            "estimated_benefit": f"+{total_balance * 0.08 / 12:,.0f} ₽/мес",
            "details": {
                "current_balance": float(total_balance),
                "interest_rate": 8.0,
                "monthly_income": float(total_balance * 0.08 / 12),
                "yearly_income": float(total_balance * 0.08)
            }
        })
    
    # Recommendation 2: Savings plan if positive net savings
    if net_savings > 10000:
        recommendations.append({
            "id": "savings-recommendation",
            "type": "savings",
            "priority": "medium",
            "title": "📊 Создайте финансовую подушку безопасности",
            "description": f"Вы экономите ~{net_savings:,.0f} ₽ в месяц. Откройте накопительный счет с начислением до 7% годовых на остаток.",
            "action": "Открыть накопительный счет",
            "estimated_benefit": f"+{net_savings * 0.07 / 12:,.0f} ₽/мес",
            "details": {
                "monthly_savings": float(net_savings),
                "interest_rate": 7.0,
                "potential_income": float(net_savings * 0.07 / 12)
            }
        })
    
    # Recommendation 3: Budget optimization if high expenses
    if expenses > income * 0.8:
        recommendations.append({
            "id": "budget-recommendation",
            "type": "budget",
            "priority": "high",
            "title": "⚠️ Оптимизируйте расходы",
            "description": f"Ваши расходы составляют {(expenses/income*100):,.0f}% от доходов. Создайте бюджеты по категориям для контроля трат.",
            "action": "Создать бюджет",
            "estimated_benefit": f"Экономия до {expenses * 0.15:,.0f} ₽/мес",
            "details": {
                "monthly_income": float(income),
                "monthly_expenses": float(expenses),
                "expense_ratio": float(expenses / income * 100) if income > 0 else 0,
                "potential_savings": float(expenses * 0.15)
            }
        })
    
    # Recommendation 4: Credit card cashback
    if expenses > 30000:
        recommendations.append({
            "id": "cashback-recommendation",
            "type": "credit_card",
            "priority": "medium",
            "title": "💳 Оформите карту с кэшбэком",
            "description": f"При тратах ~{expenses:,.0f} ₽/мес с кэшбэком 3% вы будете возвращать {expenses * 0.03:,.0f} ₽ ежемесячно.",
            "action": "Подобрать карту",
            "estimated_benefit": f"+{expenses * 0.03:,.0f} ₽/мес",
            "details": {
                "monthly_spending": float(expenses),
                "cashback_rate": 3.0,
                "monthly_cashback": float(expenses * 0.03),
                "yearly_cashback": float(expenses * 0.03 * 12)
            }
        })
    
    # Recommendation 5: Investment if stable income and good savings
    if income > 80000 and net_savings > 20000:
        recommendations.append({
            "id": "investment-recommendation",
            "type": "investment",
            "priority": "low",
            "title": "📈 Рассмотрите инвестиционные продукты",
            "description": f"Со стабильным доходом {income:,.0f} ₽/мес вы можете начать инвестировать через ИИС с налоговым вычетом до 52,000 ₽.",
            "action": "Открыть ИИС",
            "estimated_benefit": "Налоговый вычет до 52,000 ₽/год",
            "details": {
                "monthly_income": float(income),
                "recommended_investment": float(min(net_savings * 0.5, 400000 / 12)),
                "max_tax_deduction": 52000
            }
        })
    
    return recommendations

