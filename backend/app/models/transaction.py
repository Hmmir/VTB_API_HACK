"""Transaction model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database import Base


class TransactionType(str, Enum):
    """Transaction type enum."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class Transaction(Base):
    """Transaction model - financial transactions."""
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Transaction identifiers
    external_transaction_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Transaction details
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, default="RUB")  # ISO 4217 currency code
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    description = Column(Text, nullable=True)
    merchant = Column(String(255), nullable=True)
    mcc_code = Column(String(10), nullable=True)  # Merchant Category Code
    
    # Dates
    transaction_date = Column(DateTime, nullable=False, index=True)
    posted_date = Column(DateTime, nullable=True)
    
    # Metadata
    is_pending = Column(Integer, default=0)  # Using Integer as Boolean proxy
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, type={self.transaction_type}, date={self.transaction_date})>"

