"""Transaction schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: int
    account_id: int
    category_id: Optional[int]
    amount: Decimal
    transaction_type: str
    description: Optional[str]
    merchant: Optional[str]
    transaction_date: datetime
    is_pending: int
    
    class Config:
        from_attributes = True


class TransactionFilter(BaseModel):
    """Schema for filtering transactions."""
    account_ids: Optional[list[int]] = None
    category_ids: Optional[list[int]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    transaction_type: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

