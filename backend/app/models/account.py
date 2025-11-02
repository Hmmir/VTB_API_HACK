"""Account model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database import Base


class AccountType(str, Enum):
    """Account type enum."""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    INVESTMENT = "investment"
    LOAN = "loan"


class Currency(str, Enum):
    """Currency enum."""
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class Account(Base):
    """Account model - bank accounts, cards, etc."""
    
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    bank_connection_id = Column(Integer, ForeignKey("bank_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Account identifiers
    external_account_id = Column(String(255), nullable=False)  # ID at the bank
    account_number = Column(String(255), nullable=True)  # Masked: **** 1234
    account_name = Column(String(255), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    
    # Balance
    balance = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    currency = Column(SQLEnum(Currency), default=Currency.RUB, nullable=False)
    credit_limit = Column(Numeric(precision=15, scale=2), nullable=True)  # For credit accounts
    
    # Metadata
    is_active = Column(Integer, default=1)  # Using Integer as Boolean proxy
    last_synced_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    bank_connection = relationship("BankConnection", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.account_name}', type={self.account_type}, balance={self.balance})>"

