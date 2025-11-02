"""Transaction endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.schemas.transaction import TransactionResponse
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.account import Account

router = APIRouter()


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transactions with optional filters."""
    # Build query - join Account and BankConnection to filter by user
    query = db.query(Transaction).join(Account).join(Account.bank_connection).filter(
        Account.bank_connection.has(user_id=current_user.id)
    )
    
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    
    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date)
            query = query.filter(Transaction.transaction_date >= from_dt)
        except:
            pass
    
    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date)
            query = query.filter(Transaction.transaction_date <= to_dt)
        except:
            pass
    
    # Order by date desc and limit
    transactions = query.order_by(Transaction.transaction_date.desc()).limit(limit).all()
    
    return transactions

