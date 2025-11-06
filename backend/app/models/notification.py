"""Notification system models."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from uuid import uuid4
from sqlalchemy import Column, Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


def _gen_uuid() -> str:
    return str(uuid4())


class NotificationType(str, Enum):
    """Notification type classification."""
    PAYMENT_DUE = "payment_due"  # Upcoming payment
    PAYMENT_OVERDUE = "payment_overdue"  # Missed payment
    PAYMENT_RECEIVED = "payment_received"  # Payment confirmed
    CONSENT_REQUEST = "consent_request"  # New consent request
    CONSENT_EXPIRING = "consent_expiring"  # Consent about to expire
    TRANSFER_COMPLETED = "transfer_completed"  # Transfer success
    TRANSFER_FAILED = "transfer_failed"  # Transfer failed
    BUDGET_EXCEEDED = "budget_exceeded"  # Budget limit reached
    GOAL_ACHIEVED = "goal_achieved"  # Savings goal reached
    PRODUCT_APPROVED = "product_approved"  # Agreement approved
    SECURITY_ALERT = "security_alert"  # Suspicious activity
    SYSTEM = "system"  # System message


class NotificationPriority(str, Enum):
    """Notification priority level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """User notification."""
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Notification details
    type = Column(SAEnum(NotificationType), nullable=False, index=True)
    priority = Column(SAEnum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Related entity (optional)
    related_entity_type = Column(String(50), nullable=True)  # e.g., "payment", "consent", "agreement"
    related_entity_id = Column(String(36), nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Action link (optional)
    action_url = Column(String(512), nullable=True)
    action_label = Column(String(100), nullable=True)
    
    # Metadata
    notification_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)  # Auto-delete after expiry
    
    # Relationships
    user = relationship("User", backref="notifications")


__all__ = [
    "Notification",
    "NotificationType",
    "NotificationPriority",
]

