"""Family Banking Hub schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.family import (
    FamilyRole,
    FamilyMemberStatus,
    FamilyBudgetPeriod,
    FamilyGoalStatus,
    FamilyTransferStatus,
    FamilyNotificationType,
)


# ==================== Family Group Schemas ====================

class FamilyGroupCreate(BaseModel):
    """Schema for creating a family group."""
    name: str = Field(..., min_length=1, max_length=255)


class FamilyGroupUpdate(BaseModel):
    """Schema for updating a family group."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class FamilyGroupResponse(BaseModel):
    """Schema for family group response."""
    id: int
    name: str
    created_by: int
    invite_code: str
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# ==================== Family Member Schemas ====================

class FamilyMemberInvite(BaseModel):
    """Schema for inviting a member."""
    invite_code: str


class FamilyMemberUpdate(BaseModel):
    """Schema for updating a family member."""
    role: Optional[FamilyRole] = None
    status: Optional[FamilyMemberStatus] = None


class FamilyMemberResponse(BaseModel):
    """Schema for family member response."""
    id: int
    family_id: int
    user_id: int
    role: FamilyRole
    status: FamilyMemberStatus
    joined_at: datetime
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== Family Member Settings Schemas ====================

class FamilyMemberSettingsUpdate(BaseModel):
    """Schema for updating member settings."""
    show_accounts: Optional[bool] = None
    default_visibility: Optional[str] = Field(None, pattern="^(full|limited)$")


class FamilyMemberSettingsResponse(BaseModel):
    """Schema for member settings response."""
    id: int
    member_id: int
    show_accounts: bool
    default_visibility: str
    custom_limits: Optional[dict] = None
    
    class Config:
        from_attributes = True


# ==================== Family Budget Schemas ====================

class FamilyBudgetCreate(BaseModel):
    """Schema for creating a family budget."""
    category_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0)
    period: FamilyBudgetPeriod
    start_date: datetime
    end_date: Optional[datetime] = None


class FamilyBudgetUpdate(BaseModel):
    """Schema for updating a family budget."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[Decimal] = Field(None, gt=0)
    period: Optional[FamilyBudgetPeriod] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class FamilyBudgetResponse(BaseModel):
    """Schema for family budget response."""
    id: int
    family_id: int
    category_id: Optional[int]
    name: str
    amount: Decimal
    period: FamilyBudgetPeriod
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    created_at: datetime
    current_spending: Optional[Decimal] = Decimal(0)
    category_name: Optional[str] = None
    usage_percentage: Optional[float] = 0.0
    
    class Config:
        from_attributes = True


# ==================== Family Member Limit Schemas ====================

class FamilyMemberLimitCreate(BaseModel):
    """Schema for creating a member limit."""
    member_id: int
    category_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0)
    period: FamilyBudgetPeriod
    auto_unlock: bool = False


class FamilyMemberLimitUpdate(BaseModel):
    """Schema for updating a member limit."""
    amount: Optional[Decimal] = Field(None, gt=0)
    period: Optional[FamilyBudgetPeriod] = None
    auto_unlock: Optional[bool] = None
    status: Optional[str] = None


class FamilyMemberLimitResponse(BaseModel):
    """Schema for member limit response."""
    id: int
    family_id: int
    member_id: int
    category_id: Optional[int]
    amount: Decimal
    period: FamilyBudgetPeriod
    auto_unlock: bool
    status: str
    created_at: datetime
    current_spending: Optional[Decimal] = Decimal(0)
    member_name: Optional[str] = None
    category_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== Family Goal Schemas ====================

class FamilyGoalCreate(BaseModel):
    """Schema for creating a family goal."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_amount: Decimal = Field(..., gt=0)
    deadline: Optional[datetime] = None


class FamilyGoalUpdate(BaseModel):
    """Schema for updating a family goal."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_amount: Optional[Decimal] = Field(None, gt=0)
    deadline: Optional[datetime] = None
    status: Optional[FamilyGoalStatus] = None


class FamilyGoalContributionCreate(BaseModel):
    """Schema for creating a goal contribution."""
    amount: Decimal = Field(..., gt=0)
    source_account_id: int  # Обязательный - счет источник


class FamilyGoalContributionResponse(BaseModel):
    """Schema for goal contribution response."""
    id: int
    goal_id: int
    member_id: int
    amount: Decimal
    source_account_id: Optional[int]
    created_at: datetime
    member_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class FamilyGoalResponse(BaseModel):
    """Schema for family goal response."""
    id: int
    family_id: int
    name: str
    description: Optional[str]
    target_amount: Decimal
    current_amount: Decimal
    deadline: Optional[datetime]
    status: FamilyGoalStatus
    created_by: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    progress_percentage: Optional[float] = 0
    contributions: Optional[List[FamilyGoalContributionResponse]] = []
    
    class Config:
        from_attributes = True


# ==================== Family Transfer Schemas ====================

class FamilyTransferCreate(BaseModel):
    """Schema for creating a family transfer."""
    to_member_id: Optional[int] = None  # Опционально если указан to_account_id
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None  # Можно указать конкретный счет вместо участника
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="RUB", max_length=3)
    description: Optional[str] = None


class FamilyTransferApprove(BaseModel):
    """Schema for approving/rejecting a transfer."""
    approved: bool
    reason: Optional[str] = None


class FamilyTransferResponse(BaseModel):
    """Schema for family transfer response."""
    id: int
    family_id: int
    from_member_id: int
    to_member_id: Optional[int]  # Может быть None если перевод на конкретный счет
    from_account_id: Optional[int]
    to_account_id: Optional[int]
    amount: Decimal
    currency: str
    description: Optional[str]
    status: FamilyTransferStatus
    created_at: datetime
    executed_at: Optional[datetime]
    approved_by: Optional[int]
    from_member_name: Optional[str] = None
    to_member_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== Family Notification Schemas ====================

class FamilyNotificationResponse(BaseModel):
    """Schema for family notification response."""
    id: int
    family_id: int
    member_id: Optional[int]
    type: FamilyNotificationType
    payload: dict
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Family Activity Log Schemas ====================

class FamilyActivityLogResponse(BaseModel):
    """Schema for family activity log response."""
    id: int
    family_id: int
    actor_id: Optional[int]
    action: str
    target: Optional[str]
    action_metadata: Optional[dict]
    timestamp: datetime
    actor_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== Family Analytics Schemas ====================

class FamilyAnalyticsSummary(BaseModel):
    """Schema for family analytics summary."""
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    budget_usage: List[dict]
    limit_usage: List[dict]
    goal_progress: List[dict]
    top_categories: List[dict]
    member_spending: List[dict]


class FamilyMemberSpending(BaseModel):
    """Schema for member spending breakdown."""
    member_id: int
    member_name: str
    total_spending: Decimal
    category_breakdown: List[dict]
    limit_status: Optional[dict] = None

