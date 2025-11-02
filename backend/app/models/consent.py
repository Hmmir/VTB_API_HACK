"""Consent management models for OpenBanking."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class ConsentStatus(str, Enum):
    """Consent lifecycle status."""
    REQUESTED = "requested"
    APPROVED = "approved"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    REJECTED = "rejected"


class ConsentScope(str, Enum):
    """Consent permission scopes."""
    ACCOUNTS_READ = "accounts.read"
    TRANSACTIONS_READ = "transactions.read"
    BALANCES_READ = "balances.read"
    PAYMENTS_WRITE = "payments.write"
    PRODUCTS_READ = "products.read"


class PartnerBank(Base):
    """External bank that can request consents."""
    __tablename__ = "partner_banks"
    
    id = Column(String(36), primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    api_endpoint = Column(String(512), nullable=True)
    jwks_uri = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    consent_requests = relationship("ConsentRequest", back_populates="partner_bank")
    consents = relationship("Consent", back_populates="partner_bank")


class ConsentRequest(Base):
    """Request for user consent to access their data."""
    __tablename__ = "consent_requests"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_bank_id = Column(String(36), ForeignKey("partner_banks.id", ondelete="CASCADE"), nullable=False)
    
    scopes = Column(JSON, nullable=False)  # List of ConsentScope values
    purpose = Column(Text, nullable=True)
    status = Column(SAEnum(ConsentStatus), default=ConsentStatus.REQUESTED, nullable=False)
    
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    decided_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="consent_requests")
    partner_bank = relationship("PartnerBank", back_populates="consent_requests")
    consent = relationship("Consent", back_populates="request", uselist=False)


class Consent(Base):
    """Active consent granted by user."""
    __tablename__ = "consents"
    
    id = Column(String(36), primary_key=True)
    request_id = Column(String(36), ForeignKey("consent_requests.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_bank_id = Column(String(36), ForeignKey("partner_banks.id", ondelete="CASCADE"), nullable=False)
    
    scopes = Column(JSON, nullable=False)
    status = Column(SAEnum(ConsentStatus), default=ConsentStatus.ACTIVE, nullable=False, index=True)
    
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="consents")
    partner_bank = relationship("PartnerBank", back_populates="consents")
    request = relationship("ConsentRequest", back_populates="consent")
    events = relationship("ConsentEvent", back_populates="consent", order_by="ConsentEvent.created_at.desc()")


class ConsentEvent(Base):
    """Audit log for consent lifecycle events."""
    __tablename__ = "consent_events"
    
    id = Column(Integer, primary_key=True, index=True)
    consent_id = Column(String(36), ForeignKey("consents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False)  # e.g., 'granted', 'revoked', 'accessed'
    description = Column(Text, nullable=True)
    event_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    consent = relationship("Consent", back_populates="events")


__all__ = [
    "PartnerBank",
    "ConsentRequest",
    "Consent",
    "ConsentEvent",
    "ConsentStatus",
    "ConsentScope",
]

