"""Bank connection schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BankConnectionCreate(BaseModel):
    """Schema for creating a bank connection."""
    bank_provider: str
    authorization_code: str


class BankConnectionResponse(BaseModel):
    """Schema for bank connection response."""
    id: int
    bank_provider: str
    status: str
    last_synced_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

