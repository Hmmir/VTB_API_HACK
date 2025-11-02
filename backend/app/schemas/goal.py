"""Goal schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class GoalCreate(BaseModel):
    """Schema for creating a goal."""
    name: str
    description: Optional[str] = None
    target_amount: Decimal
    current_amount: Optional[Decimal] = 0
    target_date: Optional[datetime] = None
    status: Optional[str] = 'IN_PROGRESS'


class GoalUpdate(BaseModel):
    """Schema for updating a goal."""
    name: Optional[str] = None
    description: Optional[str] = None
    target_amount: Optional[Decimal] = None
    current_amount: Optional[Decimal] = None
    target_date: Optional[datetime] = None
    status: Optional[str] = None


class GoalResponse(BaseModel):
    """Schema for goal response."""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    target_amount: Decimal
    current_amount: Decimal
    target_date: Optional[datetime]
    status: str
    completed_at: Optional[datetime]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

