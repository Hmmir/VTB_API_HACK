"""Payment and Interbank Transfer models."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from uuid import uuid4
from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.account import Currency


def _gen_uuid() -> str:
    return str(uuid4())


class PaymentType(str, Enum):
    """Payment type classification."""
    INTERNAL = "internal"  # Between user's own accounts
    INTERBANK = "interbank"  # To another bank (requires consent)
    PARTNER = "partner"  # To partner service (requires consent)


class PaymentStatus(str, Enum):
    """Payment lifecycle status."""
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InterbankTransferStatus(str, Enum):
    """Interbank transfer status."""
    INITIATED = "initiated"
    PENDING_SETTLEMENT = "pending_settlement"
    SETTLED = "settled"
    FAILED = "failed"


class Payment(Base):
    """Payment record for all types of transfers."""
    __tablename__ = "payments"
    
    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    
    # Optional: link to interbank transfer if applicable
    interbank_transfer_id = Column(String(36), ForeignKey("interbank_transfers.id", ondelete="SET NULL"), nullable=True)
    
    # Payment details
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    currency = Column(SAEnum(Currency), nullable=False)
    counterparty = Column(String(255), nullable=True)  # Recipient name/identifier
    description = Column(Text, nullable=True)
    
    # Classification
    payment_type = Column(SAEnum(PaymentType), default=PaymentType.INTERNAL, nullable=False, index=True)
    status = Column(SAEnum(PaymentStatus), default=PaymentStatus.CREATED, nullable=False, index=True)
    
    # Consent (required for interbank/partner)
    consent_id = Column(String(36), ForeignKey("consents.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    payment_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="payments")
    account = relationship("Account", backref="payments")
    consent = relationship("Consent", backref="payments")
    interbank_transfer = relationship("InterbankTransfer", back_populates="payment", uselist=False)


class InterbankTransfer(Base):
    """Interbank transfer with consent validation."""
    __tablename__ = "interbank_transfers"
    
    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    from_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    
    # Partner bank
    partner_bank_id = Column(String(36), ForeignKey("partner_banks.id", ondelete="SET NULL"), nullable=True)
    
    # Counterparty (recipient)
    counterparty_account = Column(String(64), nullable=False)
    counterparty_name = Column(String(255), nullable=True)
    
    # Transfer details
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    currency = Column(SAEnum(Currency), nullable=False)
    purpose = Column(Text, nullable=True)
    
    # Consent (REQUIRED for interbank)
    consent_id = Column(String(36), ForeignKey("consents.id", ondelete="SET NULL"), nullable=False)
    
    # Status
    status = Column(SAEnum(InterbankTransferStatus), default=InterbankTransferStatus.INITIATED, nullable=False, index=True)
    
    # Metadata
    transfer_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    initiated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    settled_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="interbank_transfers")
    from_account = relationship("Account", foreign_keys=[from_account_id], backref="interbank_transfers_from")
    partner_bank = relationship("PartnerBank", backref="interbank_transfers")
    consent = relationship("Consent", backref="interbank_transfers")
    payment = relationship("Payment", back_populates="interbank_transfer", uselist=False)


__all__ = [
    "Payment",
    "PaymentType",
    "PaymentStatus",
    "InterbankTransfer",
    "InterbankTransferStatus",
]

