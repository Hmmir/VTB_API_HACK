"""Recommendation schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RecommendationResponse(BaseModel):
    """Schema for recommendation response."""
    id: int
    user_id: int
    recommendation_type: str
    title: str
    description: str
    estimated_savings: Optional[str]
    priority: int
    status: str
    viewed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

