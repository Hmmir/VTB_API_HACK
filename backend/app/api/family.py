"""Family Banking Hub API endpoints."""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.family import FamilyNotification, FamilyActivityLog, FamilyMember
from app.schemas.family import (
    FamilyGroupCreate,
    FamilyGroupUpdate,
    FamilyGroupResponse,
    FamilyMemberInvite,
    FamilyMemberUpdate,
    FamilyMemberResponse,
    FamilyBudgetCreate,
    FamilyBudgetUpdate,
    FamilyBudgetResponse,
    FamilyMemberLimitCreate,
    FamilyMemberLimitUpdate,
    FamilyMemberLimitResponse,
    FamilyGoalCreate,
    FamilyGoalUpdate,
    FamilyGoalContributionCreate,
    FamilyGoalResponse,
    FamilyTransferCreate,
    FamilyTransferApprove,
    FamilyTransferResponse,
    FamilyNotificationResponse,
    FamilyActivityLogResponse,
    FamilyAnalyticsSummary,
)
from app.services.family_service import FamilyService
from app.services.family_budget_service import FamilyBudgetService
from app.services.family_goal_service import FamilyGoalService
from app.services.family_transfer_service import FamilyTransferService
from app.services.family_analytics_service import FamilyAnalyticsService

router = APIRouter(prefix="/family", tags=["Family Banking Hub"])


# ==================== Family Group Endpoints ====================

@router.post("/groups", response_model=FamilyGroupResponse, status_code=status.HTTP_201_CREATED)
def create_family_group(
    data: FamilyGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new family group."""
    family = FamilyService.create_family(db, current_user.id, data)
    return {
        **family.__dict__,
        "member_count": len(family.members)
    }


@router.get("/groups", response_model=List[FamilyGroupResponse])
def get_user_families(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all families where user is a member."""
    families = FamilyService.get_user_families(db, current_user.id)
    return [
        {**f.__dict__, "member_count": len(f.members)}
        for f in families
    ]


@router.get("/groups/{family_id}", response_model=FamilyGroupResponse)
def get_family(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get family details."""
    if not FamilyService.is_member(db, family_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this family"
        )
    
    family = FamilyService.get_family(db, family_id)
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family not found"
        )
    
    return {**family.__dict__, "member_count": len(family.members)}


@router.patch("/groups/{family_id}", response_model=FamilyGroupResponse)
def update_family(
    family_id: int,
    data: FamilyGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update family group."""
    family = FamilyService.update_family(db, family_id, data, current_user.id)
    return {**family.__dict__, "member_count": len(family.members)}


@router.delete("/groups/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_family(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete family group."""
    FamilyService.delete_family(db, family_id, current_user.id)


@router.post("/groups/{family_id}/invite", response_model=dict)
def regenerate_invite_code(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate invite code for family."""
    if not FamilyService.is_admin(db, family_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can regenerate invite code"
        )
    
    family = FamilyService.regenerate_invite_code(db, family_id, current_user.id)
    return {"invite_code": family.invite_code}


# ==================== Family Member Endpoints ====================

@router.post("/join", response_model=FamilyMemberResponse)
def join_family_by_code(
    data: FamilyMemberInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join family using invite code (without knowing family_id)."""
    member = FamilyService.join_family(db, data.invite_code, current_user.id)
    return FamilyMemberResponse(
        id=member.id,
        family_id=member.family_id,
        user_id=member.user_id,
        role=member.role,
        status=member.status,
        joined_at=member.joined_at,
        user_name=member.user.full_name if member.user else None,
        user_email=member.user.email if member.user else None
    )


@router.post("/groups/{family_id}/members/join", response_model=FamilyMemberResponse)
def join_family(
    family_id: int,
    data: FamilyMemberInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join family using invite code (legacy endpoint with family_id in URL)."""
    member = FamilyService.join_family(db, data.invite_code, current_user.id)
    return {
        **member.__dict__,
        "user_name": member.user.full_name if member.user else None,
        "user_email": member.user.email if member.user else None
    }


@router.post("/groups/{family_id}/members/{member_id}/shared-accounts", status_code=status.HTTP_201_CREATED)
def add_shared_accounts(
    family_id: int,
    member_id: int,
    account_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add accounts to family shared accounts (append, not replace)."""
    FamilyService.add_shared_accounts(db, family_id, member_id, account_ids, current_user.id)
    return {"message": "Shared accounts added", "account_ids": account_ids}


@router.put("/groups/{family_id}/members/{member_id}/shared-accounts")
def set_shared_accounts(
    family_id: int,
    member_id: int,
    account_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set which accounts to share with family (replace all)."""
    FamilyService.set_shared_accounts(db, family_id, member_id, account_ids, current_user.id)
    return {"message": "Shared accounts updated", "account_ids": account_ids}


@router.delete("/groups/{family_id}/members/{member_id}/shared-accounts/{account_id}")
def remove_shared_account(
    family_id: int,
    member_id: int,
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a specific account from family shared accounts."""
    from app.models.family import FamilySharedAccount, FamilyActivityLog
    from sqlalchemy import and_
    
    # Verify member belongs to family and user owns the member record
    member = db.query(FamilyMember).filter(
        and_(
            FamilyMember.id == member_id,
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id
        )
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found or unauthorized"
        )
    
    # Delete the shared account
    deleted = db.query(FamilySharedAccount).filter(
        and_(
            FamilySharedAccount.family_id == family_id,
            FamilySharedAccount.member_id == member_id,
            FamilySharedAccount.account_id == account_id
        )
    ).delete()
    
    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared account not found"
        )
    
    # Log activity
    log = FamilyActivityLog(
        family_id=family_id,
        actor_id=current_user.id,
        action="removed_shared_account",
        target="family_member",
        action_metadata={"member_id": member_id, "account_id": account_id}
    )
    db.add(log)
    
    db.commit()
    return {"message": "Shared account removed", "account_id": account_id}


@router.get("/groups/{family_id}/shared-accounts")
def get_family_shared_accounts(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all shared accounts for a family group."""
    from app.models.family import FamilySharedAccount
    from app.models.account import Account
    
    # Verify membership
    member = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_id,
        FamilyMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this family"
        )
    
    # Get shared accounts
    shared_accounts = db.query(FamilySharedAccount).filter(
        FamilySharedAccount.family_id == family_id
    ).all()
    
    # Build response with account details
    result = []
    for shared in shared_accounts:
        account = db.query(Account).filter(Account.id == shared.account_id).first()
        if account:
            # Get bank name
            bank_name_map = {
                "vbank": "VBank",
                "abank": "ABank",
                "sbank": "SBank",
                "mybank": "MyBank"
            }
            # Если нет подключения, это MyBank счет
            if not account.bank_connection:
                provider = "mybank"
                bank_display_name = "MyBank"
            else:
                provider = account.bank_connection.bank_provider.value
                bank_display_name = bank_name_map.get(provider, provider.upper() if provider else "Банк")
            
            result.append({
                "id": account.id,
                "bank_connection_id": account.bank_connection_id,
                "account_name": account.account_name,
                "account_number": account.account_number,
                "account_type": account.account_type,
                "balance": float(account.balance),
                "currency": account.currency,
                "bank_name": bank_display_name,
                "bank_provider": provider,
                "member_id": shared.member_id,
                "visibility": shared.visibility.value if hasattr(shared.visibility, 'value') else str(shared.visibility)
            })
    
    return result


@router.get("/groups/{family_id}/members", response_model=List[FamilyMemberResponse])
def get_family_members(
    family_id: int,
    include_pending: bool = Query(True),  # По умолчанию ВКЛЮЧАЕМ pending для отображения кнопок одобрения
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all family members."""
    if not FamilyService.is_member(db, family_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this family"
        )
    
    members = FamilyService.get_family_members(db, family_id, include_pending)
    return [
        {
            **m.__dict__,
            "user_name": m.user.full_name if m.user else None,
            "user_email": m.user.email if m.user else None
        }
        for m in members
    ]


@router.post("/groups/{family_id}/members/{member_id}/approve", response_model=FamilyMemberResponse)
def approve_member(
    family_id: int,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve pending member."""
    member = FamilyService.approve_member(db, family_id, member_id, current_user.id)
    return {
        **member.__dict__,
        "user_name": member.user.full_name if member.user else None,
        "user_email": member.user.email if member.user else None
    }


@router.post("/groups/{family_id}/members/{member_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
def reject_member(
    family_id: int,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject pending member."""
    FamilyService.reject_member(db, family_id, member_id, current_user.id)
    return None


@router.patch("/groups/{family_id}/members/{member_id}", response_model=FamilyMemberResponse)
def update_member(
    family_id: int,
    member_id: int,
    data: FamilyMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update family member."""
    member = FamilyService.update_member(db, family_id, member_id, data, current_user.id)
    return {
        **member.__dict__,
        "user_name": member.user.full_name if member.user else None,
        "user_email": member.user.email if member.user else None
    }


@router.delete("/groups/{family_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    family_id: int,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove member from family."""
    FamilyService.remove_member(db, family_id, member_id, current_user.id)


# ==================== Family Budget Endpoints ====================

@router.post("/groups/{family_id}/budgets", response_model=FamilyBudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    family_id: int,
    data: FamilyBudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create family budget."""
    budget = FamilyBudgetService.create_budget(db, family_id, data, current_user.id)
    return {**budget.__dict__, "current_spending": 0}


@router.get("/groups/{family_id}/budgets", response_model=List[FamilyBudgetResponse])
def get_budgets(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all family budgets."""
    if not FamilyService.is_member(db, family_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this family"
        )
    
    budgets = FamilyBudgetService.get_family_budgets(db, family_id)

    now = datetime.utcnow()
    results = []

    for budget in budgets:
        period_value = budget.period.value if hasattr(budget.period, "value") else budget.period
        period_days = 7 if period_value == "weekly" else 30
        period_start = now - timedelta(days=period_days)
        start_date = max(budget.start_date, period_start) if budget.start_date else period_start

        spent_decimal = FamilyBudgetService._calculate_budget_spending_for_period(db, family_id, budget, start_date)
        usage_percentage = (
            float((spent_decimal / budget.amount) * 100)
            if budget.amount and budget.amount > 0
            else 0.0
        )

        results.append({
            "id": budget.id,
            "family_id": budget.family_id,
            "category_id": budget.category_id,
            "name": budget.name,
            "amount": budget.amount,
            "period": budget.period,
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "status": budget.status,
            "created_at": budget.created_at,
            "current_spending": spent_decimal,
            "category_name": budget.category.name if budget.category else None,
            "usage_percentage": usage_percentage,
        })

    return results


# ==================== Family Limit Endpoints ====================

@router.post("/groups/{family_id}/limits", response_model=FamilyMemberLimitResponse, status_code=status.HTTP_201_CREATED)
def create_limit(
    family_id: int,
    data: FamilyMemberLimitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create member limit."""
    limit = FamilyBudgetService.create_member_limit(db, family_id, data, current_user.id)
    return {**limit.__dict__, "current_spending": 0}


@router.get("/groups/{family_id}/members/{member_id}/limits", response_model=List[FamilyMemberLimitResponse])
def get_member_limits(
    family_id: int,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get member limits."""
    if not FamilyService.is_member(db, family_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this family"
        )
    
    limits = FamilyBudgetService.get_member_limits(db, family_id, member_id)
    return [
        {**l.__dict__, "current_spending": 0, "category_name": l.category.name if l.category else None}
        for l in limits
    ]


# ==================== Family Goal Endpoints ====================

@router.post("/groups/{family_id}/goals", response_model=FamilyGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    family_id: int,
    data: FamilyGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create family goal with MyBank account."""
    goal = await FamilyGoalService.create_goal(db, family_id, data, current_user.id)
    progress = float((goal.current_amount / goal.target_amount) * 100) if goal.target_amount > 0 else 0
    return {**goal.__dict__, "progress_percentage": progress, "contributions": []}


@router.get("/groups/{family_id}/goals", response_model=List[FamilyGoalResponse])
def get_goals(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all family goals."""
    if not FamilyService.is_member(db, family_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this family"
        )
    
    goals = FamilyGoalService.get_family_goals(db, family_id)
    return [
        {
            **g.__dict__,
            "progress_percentage": float((g.current_amount / g.target_amount) * 100) if g.target_amount > 0 else 0,
            "contributions": []
        }
        for g in goals
    ]


@router.post("/groups/{family_id}/goals/{goal_id}/contributions", status_code=status.HTTP_201_CREATED)
async def contribute_to_goal(
    family_id: int,
    goal_id: int,
    data: FamilyGoalContributionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Make contribution to goal."""
    member = FamilyService.get_member_by_user(db, family_id, current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this family"
        )
    
    contribution = await FamilyGoalService.contribute_to_goal(
        db, goal_id, member.id, data, current_user.id
    )
    return {"message": "Contribution successful", "contribution_id": contribution.id}


# ==================== Family Transfer Endpoints ====================

@router.post("/groups/{family_id}/transfers", response_model=FamilyTransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    family_id: int,
    data: FamilyTransferCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create family transfer."""
    member = FamilyService.get_member_by_user(db, family_id, current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this family"
        )
    
    transfer = FamilyTransferService.create_transfer(
        db, family_id, member.id, data, current_user.id
    )
    return {**transfer.__dict__}


@router.post("/groups/{family_id}/transfers/{transfer_id}/approve", response_model=FamilyTransferResponse)
def approve_transfer(
    family_id: int,
    transfer_id: int,
    data: FamilyTransferApprove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve or reject transfer."""
    transfer = FamilyTransferService.approve_transfer(db, transfer_id, data, current_user.id)
    return {**transfer.__dict__}


@router.get("/groups/{family_id}/transfers", response_model=List[FamilyTransferResponse])
def get_transfers(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get family transfers."""
    if not FamilyService.is_member(db, family_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this family"
        )
    
    transfers = FamilyTransferService.get_family_transfers(db, family_id)
    return [
        {
            **t.__dict__,
            "from_member_name": t.from_member.user.full_name if t.from_member and t.from_member.user else None,
            "to_member_name": t.to_member.user.full_name if t.to_member and t.to_member.user else None
        }
        for t in transfers
    ]


# ==================== Analytics Endpoints ====================

@router.get("/groups/{family_id}/analytics/summary", response_model=FamilyAnalyticsSummary)
def get_analytics_summary(
    family_id: int,
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get family analytics summary."""
    if not FamilyService.is_member(db, family_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this family"
        )
    
    return FamilyAnalyticsService.get_family_summary(db, family_id, period_days)


# ==================== Notification Endpoints ====================

@router.get("/groups/{family_id}/notifications", response_model=List[FamilyNotificationResponse])
def get_notifications(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get family notifications."""
    member = FamilyService.get_member_by_user(db, family_id, current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this family"
        )
    
    notifications = db.query(FamilyNotification).filter(
        FamilyNotification.family_id == family_id,
        (FamilyNotification.member_id == member.id) | (FamilyNotification.member_id.is_(None))
    ).order_by(FamilyNotification.created_at.desc()).limit(50).all()
    
    return [n.__dict__ for n in notifications]


# ==================== Activity Log Endpoints ====================

@router.get("/groups/{family_id}/activity", response_model=List[FamilyActivityLogResponse])
def get_activity_log(
    family_id: int,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get family activity log."""
    if not FamilyService.is_member(db, family_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this family"
        )
    
    logs = db.query(FamilyActivityLog).filter(
        FamilyActivityLog.family_id == family_id
    ).order_by(FamilyActivityLog.timestamp.desc()).limit(limit).all()
    
    return [
        {
            **log.__dict__,
            "actor_name": log.actor.full_name if log.actor else None
        }
        for log in logs
    ]

