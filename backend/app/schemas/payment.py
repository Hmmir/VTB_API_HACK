"""Pydantic schemas for payments and interbank transfers."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from app.models.account import Currency
from app.models.payment import PaymentType, PaymentStatus, InterbankTransferStatus


# Payment Schemas
class PaymentCreate(BaseModel):
    """Create internal payment."""
    account_id: int
    amount: Decimal = Field(..., gt=0)
    currency: Currency
    counterparty: Optional[str] = None
    description: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment details."""
    id: str
    user_id: int
    account_id: int
    amount: Decimal
    currency: Currency
    counterparty: Optional[str]
    description: Optional[str]
    payment_type: PaymentType
    status: PaymentStatus
    consent_id: Optional[str]
    payment_metadata: Optional[dict]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Interbank Transfer Schemas
class InterbankTransferCreate(BaseModel):
    """Create interbank transfer (requires consent)."""
    from_account_id: int
    partner_bank_code: str
    counterparty_account: str = Field(..., min_length=1, max_length=64)
    counterparty_name: Optional[str] = Field(None, max_length=255)
    amount: Decimal = Field(..., gt=0)
    currency: Currency
    purpose: Optional[str] = None
    consent_id: str = Field(..., description="Required: active consent ID")


class InterbankTransferResponse(BaseModel):
    """Interbank transfer details."""
    id: str
    user_id: int
    from_account_id: int
    partner_bank_id: Optional[str]
    partner_bank_code: Optional[str]
    counterparty_account: str
    counterparty_name: Optional[str]
    amount: Decimal
    currency: Currency
    purpose: Optional[str]
    consent_id: str
    status: InterbankTransferStatus
    transfer_metadata: Optional[dict]
    initiated_at: datetime
    settled_at: Optional[datetime]

    class Config:
        from_attributes = True


class InterbankTransferStatusUpdate(BaseModel):
    """Update interbank transfer status (for webhooks/admin)."""
    status: InterbankTransferStatus
    settled_at: Optional[datetime] = None
    metadata: Optional[dict] = None


# Improved internal transfer (replacing old accounts/transfer)
class InternalTransferRequest(BaseModel):
    """Internal transfer between user's accounts."""
    from_account_id: int
    to_account_id: int
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None


class InternalTransferResponse(BaseModel):
    """Internal transfer result."""
    payment_id: str
    from_account_id: int
    to_account_id: int
    amount: Decimal
    currency: Currency
    description: Optional[str]
    status: PaymentStatus
    created_at: datetime
    message: str = "Internal transfer completed"


__all__ = [
    "PaymentCreate",
    "PaymentResponse",
    "InterbankTransferCreate",
    "InterbankTransferResponse",
    "InterbankTransferStatusUpdate",
    "InternalTransferRequest",
    "InternalTransferResponse",
]

