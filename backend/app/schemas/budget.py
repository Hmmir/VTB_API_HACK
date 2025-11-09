"""Budget schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class BudgetCreate(BaseModel):
    """Schema for creating a budget."""
    name: str
    category_id: int
    amount: Decimal
    period: Optional[str] = "monthly"
    start_date: datetime
    end_date: datetime


class BudgetUpdate(BaseModel):
    """Schema for updating a budget."""
    category_id: Optional[int] = None
    amount: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BudgetResponse(BaseModel):
    """Schema for budget response."""
    id: int
    user_id: int
    category_id: Optional[int]
    name: str
    amount: Decimal
    period: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime]
    is_active: int
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

