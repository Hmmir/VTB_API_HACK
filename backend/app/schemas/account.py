"""Account schemas."""
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal


class AccountResponse(BaseModel):
    """Schema for account response."""
    id: int
    bank_connection_id: int
    account_name: str
    account_number: Optional[str]
    account_type: str
    balance: Decimal
    currency: str
    credit_limit: Optional[Decimal]
    is_active: int
    last_synced_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AccountTransferRequest(BaseModel):
    """Schema for transferring funds between accounts."""

    from_account_id: int
    to_account_id: int
    amount: Decimal
    description: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Amount must be greater than zero")
        return value


class AccountTransferResponse(BaseModel):
    """Schema for transfer response."""

    transaction_id: int
    mirror_transaction_id: int
    message: str
