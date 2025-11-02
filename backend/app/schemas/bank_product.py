"""Bank product schemas."""
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class BankProductResponse(BaseModel):
    """Schema for bank product response."""
    id: int
    bank_provider: str
    product_type: str
    name: str
    description: Optional[str]
    interest_rate: Optional[Decimal]
    min_amount: Optional[Decimal]
    max_amount: Optional[Decimal]
    term_months: Optional[int]
    url: Optional[str]
    
    class Config:
        from_attributes = True

