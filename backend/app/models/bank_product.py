"""Bank product model."""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, Enum as SQLEnum
from datetime import datetime
from enum import Enum
from app.database import Base


class ProductType(str, Enum):
    """Product type enum."""
    DEPOSIT = "deposit"
    LOAN = "loan"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"


class BankProduct(Base):
    """Bank product model - available financial products."""
    
    __tablename__ = "bank_products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    bank_provider = Column(String(50), nullable=False, index=True)
    product_type = Column(SQLEnum(ProductType), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Product parameters
    interest_rate = Column(Numeric(precision=5, scale=2), nullable=True)  # Annual percentage
    min_amount = Column(Numeric(precision=15, scale=2), nullable=True)
    max_amount = Column(Numeric(precision=15, scale=2), nullable=True)
    term_months = Column(Integer, nullable=True)
    
    # Additional info
    features = Column(Text, nullable=True)  # JSON string with features
    url = Column(String(500), nullable=True)
    
    is_active = Column(Integer, default=1)  # Using Integer as Boolean proxy
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<BankProduct(id={self.id}, name='{self.name}', type={self.product_type}, rate={self.interest_rate})>"

