"""Recommendation model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database import Base


class RecommendationType(str, Enum):
    """Recommendation type enum."""
    SAVINGS = "savings"
    INVESTMENT = "investment"
    DEBT_REDUCTION = "debt_reduction"
    BUDGET_OPTIMIZATION = "budget_optimization"
    PRODUCT_SUGGESTION = "product_suggestion"


class RecommendationStatus(str, Enum):
    """Recommendation status enum."""
    NEW = "new"
    VIEWED = "viewed"
    APPLIED = "applied"
    DISMISSED = "dismissed"


class Recommendation(Base):
    """Recommendation model - personalized financial recommendations."""
    
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    recommendation_type = Column(SQLEnum(RecommendationType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Potential impact
    estimated_savings = Column(String(100), nullable=True)  # e.g., "5000 RUB/month"
    priority = Column(Integer, default=0)  # Higher = more important
    
    status = Column(SQLEnum(RecommendationStatus), default=RecommendationStatus.NEW, nullable=False)
    
    # Additional data
    extra_data = Column(Text, nullable=True)  # JSON string with additional data
    
    viewed_at = Column(DateTime, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    
    def __repr__(self):
        return f"<Recommendation(id={self.id}, type={self.recommendation_type}, status={self.status})>"

