"""Product agreements models (deposits, credits, cards)."""
from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from uuid import uuid4
from sqlalchemy import Column, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database import Base


def _gen_uuid() -> str:
    return str(uuid4())


class ProductType(str, Enum):
    """Type of financial product."""
    DEPOSIT = "deposit"
    CREDIT = "credit"
    CARD = "card"
    LOAN = "loan"
    MORTGAGE = "mortgage"


class AgreementStatus(str, Enum):
    """Agreement lifecycle status."""
    DRAFT = "draft"  # Created but not signed
    ACTIVE = "active"  # Signed and active
    SUSPENDED = "suspended"  # Temporarily suspended
    CLOSED = "closed"  # Completed or closed
    CANCELLED = "cancelled"  # Cancelled before activation


class PaymentScheduleType(str, Enum):
    """Payment schedule type for credits."""
    ANNUITY = "annuity"  # Equal payments
    DIFFERENTIATED = "differentiated"  # Decreasing payments
    BULLET = "bullet"  # Pay at end
    CUSTOM = "custom"


class ProductAgreement(Base):
    """Contract between user and bank for a financial product."""
    __tablename__ = "product_agreements"
    
    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_product_id = Column(String(255), nullable=True)  # External bank API product ID (e.g. "prod-vbank-deposit-001")
    
    # Agreement details
    agreement_number = Column(String(50), unique=True, nullable=False)
    product_type = Column(SAEnum(ProductType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    status = Column(SAEnum(AgreementStatus, values_callable=lambda x: [e.value for e in x]), default=AgreementStatus.DRAFT, nullable=False, index=True)
    
    # Financial terms
    amount = Column(Numeric(precision=15, scale=2), nullable=False)  # Principal for credit, initial for deposit
    interest_rate = Column(Numeric(precision=5, scale=2), nullable=False)  # Annual percentage
    term_months = Column(Integer, nullable=False)  # Duration in months
    
    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    signed_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Credit-specific fields
    payment_schedule_type = Column(SAEnum(PaymentScheduleType, values_callable=lambda x: [e.value for e in x]), nullable=True)
    monthly_payment = Column(Numeric(precision=15, scale=2), nullable=True)
    outstanding_balance = Column(Numeric(precision=15, scale=2), nullable=True)
    
    # Deposit-specific fields
    accumulated_interest = Column(Numeric(precision=15, scale=2), default=Decimal("0.00"), nullable=True)
    
    # Card-specific fields
    card_number_masked = Column(String(20), nullable=True)  # e.g., "**** **** **** 1234"
    credit_limit = Column(Numeric(precision=15, scale=2), nullable=True)
    available_limit = Column(Numeric(precision=15, scale=2), nullable=True)
    
    # Linked account
    linked_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    agreement_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", backref="product_agreements")
    # Note: bank_product relationship removed - bank_product_id is now a string reference to external API
    linked_account = relationship("Account", backref="product_agreements")
    payment_schedules = relationship("PaymentSchedule", back_populates="agreement", cascade="all, delete-orphan")


class PaymentSchedule(Base):
    """Payment schedule for credits/loans."""
    __tablename__ = "payment_schedules"
    
    id = Column(String(36), primary_key=True, default=_gen_uuid)
    agreement_id = Column(String(36), ForeignKey("product_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Schedule details
    payment_number = Column(Integer, nullable=False)  # 1, 2, 3, ...
    due_date = Column(Date, nullable=False, index=True)
    
    # Amounts
    principal_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    interest_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    total_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    
    # Payment tracking
    paid_amount = Column(Numeric(precision=15, scale=2), default=Decimal("0.00"), nullable=False)
    paid_at = Column(DateTime, nullable=True)
    is_paid = Column(Boolean, default=False, nullable=False)
    is_overdue = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    payment_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    agreement = relationship("ProductAgreement", back_populates="payment_schedules")


class AgreementEvent(Base):
    """Audit log for agreement lifecycle events."""
    __tablename__ = "agreement_events"
    
    id = Column(String(36), primary_key=True, default=_gen_uuid)
    agreement_id = Column(String(36), ForeignKey("product_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False)  # e.g., "created", "signed", "payment_made", "closed"
    description = Column(Text, nullable=True)
    event_metadata = Column(JSON, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    agreement = relationship("ProductAgreement", backref="events")


__all__ = [
    "ProductAgreement",
    "ProductType",
    "AgreementStatus",
    "PaymentScheduleType",
    "PaymentSchedule",
    "AgreementEvent",
]

