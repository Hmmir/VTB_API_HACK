"""API endpoints for Family Banking Hub."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.schemas.family import (
    AccountVisibilityUpdate,
    FamilyAnalyticsSummary,
    FamilyBudgetCreate,
    FamilyBudgetResponse,
    FamilyCreate,
    FamilyDetailResponse,
    FamilyGoalContributionCreate,
    FamilyGoalContributionResponse,
    FamilyGoalCreate,
    FamilyGoalResponse,
    FamilyInviteResponse,
    FamilyJoinRequest,
    FamilyMemberLimitCreate,
    FamilyMemberLimitResponse,
    FamilyMemberResponse,
    FamilyMemberUpdateRequest,
    FamilyResponse,
    FamilyTransferApproveRequest,
    FamilyTransferCreate,
    FamilyTransferResponse,
    FamilyNotificationResponse,
)
from app.models.family import FamilyGroup
from app.models.user import User
from app.services.family_service import FamilyService


router = APIRouter(prefix="/family", tags=["Family Banking"])


def _map_family_response(family: FamilyGroup, user_id: int) -> FamilyResponse:
    member = next((m for m in family.members if m.user_id == user_id), None)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    return FamilyResponse(
        id=family.id,
        name=family.name,
        description=family.description,
        invite_code=family.invite_code,
        created_at=family.created_at,
        updated_at=family.updated_at,
        role=member.role,
        status=member.status,
    )


@router.post("/groups", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
def create_family_group(
    payload: FamilyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family = FamilyService.create_family(db, user_id=current_user.id, name=payload.name, description=payload.description)
    db.refresh(family)
    return _map_family_response(family, current_user.id)


@router.get("/groups", response_model=list[FamilyResponse])
def list_family_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    families = FamilyService.list_families(db, user_id=current_user.id)
    return [_map_family_response(family, current_user.id) for family in families]


@router.get("/groups/{family_id}", response_model=FamilyDetailResponse)
def get_family_group(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family = FamilyService.get_family(db, user_id=current_user.id, family_id=family_id)
    response = _map_family_response(family, current_user.id)
    members = [
        FamilyMemberResponse(
            id=member.id,
            user_id=member.user_id,
            role=member.role,
            status=member.status,
            joined_at=member.joined_at,
            show_accounts=member.settings.show_accounts if member.settings else True,
            default_visibility=member.settings.default_visibility if member.settings else "family",
            custom_limits=member.settings.custom_limits if member.settings else None,
        )
        for member in family.members
    ]
    return FamilyDetailResponse(**response.dict(), members=members)


@router.post("/groups/{family_id}/invite", response_model=FamilyInviteResponse)
def rotate_invite(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family = FamilyService.generate_invite(db, family_id=family_id, user_id=current_user.id)
    return FamilyInviteResponse(family_id=family.id, invite_code=family.invite_code)


@router.post("/groups/join", response_model=FamilyResponse)
def join_family(
    payload: FamilyJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family = FamilyService.join_family(db, user_id=current_user.id, invite_code=payload.invite_code)
    return _map_family_response(family, current_user.id)


@router.patch("/groups/{family_id}/members/{member_id}", response_model=FamilyMemberResponse)
def update_family_member(
    family_id: int,
    member_id: int,
    payload: FamilyMemberUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = FamilyService.update_member(
        db,
        family_id=family_id,
        user_id=current_user.id,
        member_id=member_id,
        role=payload.role,
        status=payload.status,
    )
    return FamilyMemberResponse(
        id=member.id,
        user_id=member.user_id,
        role=member.role,
        status=member.status,
        joined_at=member.joined_at,
        show_accounts=member.settings.show_accounts if member.settings else True,
        default_visibility=member.settings.default_visibility if member.settings else "family",
        custom_limits=member.settings.custom_limits if member.settings else None,
    )


@router.delete("/groups/{family_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_family_member(
    family_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    FamilyService.remove_member(db, family_id=family_id, user_id=current_user.id, member_id=member_id)
    return None


@router.post("/groups/{family_id}/budgets", response_model=FamilyBudgetResponse, status_code=status.HTTP_201_CREATED)
def create_family_budget(
    family_id: int,
    payload: FamilyBudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budget = FamilyService.create_budget(db, family_id=family_id, user_id=current_user.id, payload=payload)
    return FamilyBudgetResponse.from_orm(budget)


@router.get("/groups/{family_id}/budgets", response_model=list[FamilyBudgetResponse])
def list_family_budgets(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budgets = FamilyService.list_budgets(db, family_id=family_id, user_id=current_user.id)
    return [FamilyBudgetResponse.from_orm(budget) for budget in budgets]


@router.post("/groups/{family_id}/limits", response_model=FamilyMemberLimitResponse, status_code=status.HTTP_201_CREATED)
def create_member_limit(
    family_id: int,
    payload: FamilyMemberLimitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    limit_obj = FamilyService.create_member_limit(db, family_id=family_id, user_id=current_user.id, payload=payload)
    return FamilyMemberLimitResponse.from_orm(limit_obj)


@router.get("/groups/{family_id}/limits", response_model=list[FamilyMemberLimitResponse])
def list_member_limits(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    limits = FamilyService.list_member_limits(db, family_id=family_id, user_id=current_user.id)
    return [FamilyMemberLimitResponse.from_orm(limit_obj) for limit_obj in limits]


@router.post("/groups/{family_id}/goals", response_model=FamilyGoalResponse, status_code=status.HTTP_201_CREATED)
def create_family_goal(
    family_id: int,
    payload: FamilyGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = FamilyService.create_goal(db, family_id=family_id, user_id=current_user.id, payload=payload)
    return FamilyGoalResponse.from_orm(goal)


@router.get("/groups/{family_id}/goals", response_model=list[FamilyGoalResponse])
def list_family_goals(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goals = FamilyService.list_goals(db, family_id=family_id, user_id=current_user.id)
    return [FamilyGoalResponse.from_orm(goal) for goal in goals]


@router.post("/groups/{family_id}/goals/{goal_id}/contributions", response_model=FamilyGoalContributionResponse, status_code=status.HTTP_201_CREATED)
def contribute_goal(
    family_id: int,
    goal_id: int,
    payload: FamilyGoalContributionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contribution = FamilyService.contribute_goal(
        db,
        family_id=family_id,
        user_id=current_user.id,
        goal_id=goal_id,
        payload=payload,
    )
    return FamilyGoalContributionResponse.from_orm(contribution)


@router.post("/groups/{family_id}/transfers", response_model=FamilyTransferResponse, status_code=status.HTTP_201_CREATED)
def create_family_transfer(
    family_id: int,
    payload: FamilyTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transfer = FamilyService.create_transfer(
        db,
        family_id=family_id,
        user_id=current_user.id,
        payload=payload,
    )
    return FamilyTransferResponse.from_orm(transfer)


@router.post("/groups/{family_id}/transfers/{transfer_id}/decision", response_model=FamilyTransferResponse)
def approve_family_transfer(
    family_id: int,
    transfer_id: int,
    payload: FamilyTransferApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transfer = FamilyService.approve_transfer(
        db,
        family_id=family_id,
        user_id=current_user.id,
        transfer_id=transfer_id,
        approve=payload.approve,
        reason=payload.reason,
    )
    return FamilyTransferResponse.from_orm(transfer)


@router.get("/groups/{family_id}/transfers", response_model=list[FamilyTransferResponse])
def list_family_transfers(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transfers = FamilyService.list_transfers(db, family_id=family_id, user_id=current_user.id)
    return [FamilyTransferResponse.from_orm(transfer) for transfer in transfers]


@router.get("/groups/{family_id}/notifications", response_model=list[FamilyNotificationResponse])
def list_family_notifications(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifications = FamilyService.list_notifications(db, family_id=family_id, user_id=current_user.id)
    return [FamilyNotificationResponse.from_orm(notification) for notification in notifications]


@router.get("/groups/{family_id}/analytics/summary", response_model=FamilyAnalyticsSummary)
def family_analytics_summary(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = FamilyService.get_analytics_summary(db, family_id=family_id, user_id=current_user.id)
    return summary


@router.patch("/groups/{family_id}/accounts/{account_id}/visibility", response_model=AccountVisibilityUpdate)
def update_account_visibility(
    family_id: int,
    account_id: int,
    payload: AccountVisibilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fav = FamilyService.update_account_visibility(
        db,
        family_id=family_id,
        user_id=current_user.id,
        account_id=account_id,
        visibility_scope=payload.visibility_scope,
    )
    return AccountVisibilityUpdate(visibility_scope=fav.visibility_scope)


