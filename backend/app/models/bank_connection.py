"""Bank connection model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database import Base


class BankProvider(str, Enum):
    """Bank provider enum."""
    VBANK = "vbank"
    ABANK = "abank"
    SBANK = "sbank"


class ConnectionStatus(str, Enum):
    """Connection status enum."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


class BankConnection(Base):
    """Bank connection model - stores OAuth tokens and connection metadata."""
    
    __tablename__ = "bank_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_provider = Column(SQLEnum(BankProvider), nullable=False)
    bank_user_id = Column(String(255), nullable=False)  # User ID at the bank
    
    # OAuth tokens (encrypted)
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    status = Column(SQLEnum(ConnectionStatus), default=ConnectionStatus.ACTIVE, nullable=False)
    last_synced_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="bank_connections")
    accounts = relationship("Account", back_populates="bank_connection", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BankConnection(id={self.id}, user_id={self.user_id}, bank={self.bank_provider}, status={self.status})>"

