"""Budget endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.budget import Budget
from app.models.category import Category

router = APIRouter()


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new budget."""
    # Verify category exists
    category = db.query(Category).filter(Category.id == budget_data.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    budget = Budget(
        user_id=current_user.id,
        **budget_data.model_dump()
    )
    
    db.add(budget)
    db.commit()
    db.refresh(budget)
    
    return budget


@router.get("/", response_model=List[BudgetResponse])
def get_budgets(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all budgets for current user."""
    query = db.query(Budget).filter(Budget.user_id == current_user.id)
    
    if active_only:
        now = datetime.utcnow()
        query = query.filter(
            Budget.start_date <= now,
            Budget.end_date >= now
        )
    
    return query.all()


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific budget."""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    return budget


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update budget."""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    for key, value in budget_data.model_dump(exclude_unset=True).items():
        setattr(budget, key, value)
    
    db.commit()
    db.refresh(budget)
    
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete budget."""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    db.delete(budget)
    db.commit()


@router.get("/{budget_id}/status")
def get_budget_status(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get budget status with current spending."""
    from app.models.transaction import Transaction, TransactionType
    from sqlalchemy import func
    
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Calculate current spending for this category in the budget period
    from app.models.account import Account
    
    account_ids = [acc.id for acc in db.query(Account).join(Account.bank_connection).filter(
        Account.bank_connection.has(user_id=current_user.id)
    ).all()]
    
    spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.category_id == budget.category_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= budget.start_date,
        Transaction.transaction_date <= budget.end_date
    ).scalar() or 0
    
    percentage = (spent / budget.amount) * 100 if budget.amount > 0 else 0
    remaining = budget.amount - spent
    
    # Check if over limit
    is_exceeded = spent > budget.amount
    is_warning = percentage >= 80 and not is_exceeded  # Warning at 80%
    
    return {
        "budget_id": budget.id,
        "category": budget.category.name if budget.category else "Unknown",
        "limit": float(budget.amount),
        "spent": float(spent),
        "remaining": float(remaining),
        "percentage": round(percentage, 2),
        "is_exceeded": is_exceeded,
        "is_warning": is_warning,
        "period": {
            "start": budget.start_date.isoformat(),
            "end": budget.end_date.isoformat()
        }
    }

