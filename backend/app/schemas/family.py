"""Pydantic schemas for Family Banking Hub."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.family import (
    FamilyBudgetPeriod,
    FamilyBudgetStatus,
    FamilyGoalStatus,
    FamilyMemberLimitPeriod,
    FamilyMemberLimitStatus,
    FamilyMemberStatus,
    FamilyRole,
    FamilyTransferStatus,
    FamilyNotificationType,
    FamilyNotificationStatus,
)
from app.models.account import AccountVisibilityScope


class FamilyCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class FamilyInviteResponse(BaseModel):
    family_id: int
    invite_code: str


class FamilyMemberBase(BaseModel):
    id: int
    user_id: int
    role: FamilyRole
    status: FamilyMemberStatus
    joined_at: Optional[datetime]

    class Config:
        orm_mode = True


class FamilyMemberResponse(FamilyMemberBase):
    show_accounts: bool = True
    default_visibility: str = "family"
    custom_limits: Optional[dict] = None


class FamilyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    invite_code: str
    created_at: datetime
    updated_at: datetime
    role: FamilyRole
    status: FamilyMemberStatus

    class Config:
        orm_mode = True


class FamilyDetailResponse(FamilyResponse):
    members: List[FamilyMemberResponse]


class FamilyJoinRequest(BaseModel):
    invite_code: str


class FamilyMemberUpdateRequest(BaseModel):
    role: Optional[FamilyRole] = None
    status: Optional[FamilyMemberStatus] = None


class FamilyBudgetCreate(BaseModel):
    name: str
    amount: float
    period: FamilyBudgetPeriod
    category_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class FamilyBudgetResponse(BaseModel):
    id: int
    name: str
    amount: float
    period: FamilyBudgetPeriod
    status: FamilyBudgetStatus
    category_id: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class FamilyMemberLimitCreate(BaseModel):
    member_id: int
    amount: float
    period: FamilyMemberLimitPeriod
    category_id: Optional[int] = None
    auto_unlock: bool = False


class FamilyMemberLimitResponse(BaseModel):
    id: int
    member_id: int
    amount: float
    period: FamilyMemberLimitPeriod
    status: FamilyMemberLimitStatus
    category_id: Optional[int]
    auto_unlock: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class FamilyGoalCreate(BaseModel):
    name: str
    description: Optional[str]
    target_amount: float
    deadline: Optional[date]


class FamilyGoalResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    target_amount: float
    current_amount: float
    deadline: Optional[date]
    status: FamilyGoalStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class FamilyGoalContributionCreate(BaseModel):
    amount: float
    source_account_id: Optional[int] = None
    scheduled: bool = False
    schedule_rule: Optional[dict] = None


class FamilyGoalContributionResponse(BaseModel):
    id: int
    goal_id: int
    member_id: int
    amount: float
    source_account_id: Optional[int]
    scheduled: bool
    schedule_rule: Optional[dict]
    created_at: datetime

    class Config:
        orm_mode = True


class FamilyTransferCreate(BaseModel):
    to_member_id: int
    to_account_id: Optional[int]
    from_account_id: Optional[int]
    amount: float
    currency: str = "RUB"
    description: Optional[str]


class FamilyTransferApproveRequest(BaseModel):
    approve: bool
    reason: Optional[str] = None


class FamilyTransferResponse(BaseModel):
    id: int
    family_id: int
    from_member_id: Optional[int]
    to_member_id: Optional[int]
    from_account_id: Optional[int]
    to_account_id: Optional[int]
    requested_by_member_id: Optional[int]
    approved_by_member_id: Optional[int]
    amount: float
    currency: str
    description: Optional[str]
    status: FamilyTransferStatus
    created_at: datetime
    approved_at: Optional[datetime]
    executed_at: Optional[datetime]
    failed_reason: Optional[str]

    class Config:
        orm_mode = True


class FamilyNotificationResponse(BaseModel):
    id: int
    family_id: int
    member_id: Optional[int]
    notification_type: FamilyNotificationType
    payload: Optional[dict]
    status: FamilyNotificationStatus
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        orm_mode = True


class FamilyAnalyticsSummary(BaseModel):
    total_balance: float
    total_income: float
    total_expense: float
    budgets: List[dict]
    member_spending: List[dict]
    category_spending: List[dict]
    goals: List[dict]


class AccountVisibilityUpdate(BaseModel):
    visibility_scope: AccountVisibilityScope


class FamilyDashboardResponse(BaseModel):
    family: FamilyDetailResponse
    budgets: List[FamilyBudgetResponse]
    limits: List[FamilyMemberLimitResponse]
    goals: List[FamilyGoalResponse]
    transfers: List[FamilyTransferResponse]
    notifications: List[FamilyNotificationResponse]


