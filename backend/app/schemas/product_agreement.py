"""Pydantic schemas for product agreements."""
from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.product_agreement import ProductType, AgreementStatus, PaymentScheduleType


# PaymentSchedule Schemas
class PaymentScheduleResponse(BaseModel):
    """Payment schedule entry."""
    id: str
    agreement_id: str
    payment_number: int
    due_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    paid_at: Optional[datetime]
    is_paid: bool
    is_overdue: bool

    class Config:
        from_attributes = True


# ProductAgreement Schemas
class ProductAgreementCreate(BaseModel):
    """Create new product agreement (draft)."""
    bank_product_id: str  # Changed from int to str to support bank product IDs like "prod-vbank-deposit-001"
    amount: Decimal = Field(..., gt=0)
    term_months: int = Field(..., gt=0, le=360)
    linked_account_id: Optional[int] = None
    
    # Credit-specific
    payment_schedule_type: Optional[PaymentScheduleType] = None
    
    # Card-specific
    credit_limit: Optional[Decimal] = Field(None, gt=0)


class ProductAgreementSign(BaseModel):
    """Sign agreement to activate it."""
    signature: str = Field(..., min_length=10)  # Digital signature or PIN


class ProductAgreementResponse(BaseModel):
    """Product agreement details."""
    id: str
    user_id: int
    bank_product_id: Optional[str]  # Changed from int to str - external product ID
    agreement_number: str
    product_type: ProductType
    status: AgreementStatus
    
    amount: Decimal
    interest_rate: Decimal
    term_months: int
    
    start_date: date
    end_date: date
    signed_at: Optional[datetime]
    closed_at: Optional[datetime]
    
    # Credit fields
    payment_schedule_type: Optional[PaymentScheduleType]
    monthly_payment: Optional[Decimal]
    outstanding_balance: Optional[Decimal]
    
    # Deposit fields
    accumulated_interest: Optional[Decimal]
    
    # Card fields
    card_number_masked: Optional[str]
    credit_limit: Optional[Decimal]
    available_limit: Optional[Decimal]
    
    linked_account_id: Optional[int]
    agreement_metadata: Optional[dict]
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductAgreementWithSchedule(ProductAgreementResponse):
    """Agreement with full payment schedule."""
    payment_schedules: List[PaymentScheduleResponse] = []


class AgreementEventResponse(BaseModel):
    """Agreement audit event."""
    id: str
    agreement_id: str
    event_type: str
    description: Optional[str]
    event_metadata: Optional[dict]
    timestamp: datetime

    class Config:
        from_attributes = True


class AgreementListResponse(BaseModel):
    """Paginated agreements list."""
    agreements: List[ProductAgreementResponse]
    total: int


class MakePaymentRequest(BaseModel):
    """Make payment for credit/loan."""
    amount: Decimal = Field(..., gt=0)
    payment_number: Optional[int] = None  # Specific payment, or earliest unpaid


class AgreementCloseRequest(BaseModel):
    """Request to close agreement early."""
    reason: Optional[str] = None


__all__ = [
    "ProductAgreementCreate",
    "ProductAgreementSign",
    "ProductAgreementResponse",
    "ProductAgreementWithSchedule",
    "PaymentScheduleResponse",
    "AgreementEventResponse",
    "AgreementListResponse",
    "MakePaymentRequest",
    "AgreementCloseRequest",
]

