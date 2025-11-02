"""Category schemas."""
from pydantic import BaseModel
from typing import Optional


class CategoryResponse(BaseModel):
    """Schema for category response."""
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    is_system: int
    
    class Config:
        from_attributes = True

