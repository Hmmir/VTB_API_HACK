"""Goals endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.goal import Goal

router = APIRouter()


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new financial goal."""
    goal = Goal(
        user_id=current_user.id,
        **goal_data.dict()
    )
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    return goal


@router.get("/", response_model=List[GoalResponse])
def get_goals(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all goals for current user."""
    query = db.query(Goal).filter(Goal.user_id == current_user.id)
    
    if active_only:
        query = query.filter(Goal.status == 'IN_PROGRESS')
    
    return query.order_by(Goal.created_at.desc()).all()


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific goal."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update goal."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    for key, value in goal_data.dict(exclude_unset=True).items():
        setattr(goal, key, value)
    
    # Auto-complete if target reached
    if goal.current_amount >= goal.target_amount and goal.status != 'COMPLETED':
        goal.status = 'COMPLETED'
    
    db.commit()
    db.refresh(goal)
    
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete goal."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    db.delete(goal)
    db.commit()


@router.post("/{goal_id}/contribute")
def contribute_to_goal(
    goal_id: int,
    contribution: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add contribution to goal."""
    amount = contribution.get("amount")
    if not amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount is required"
        )
    
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    from decimal import Decimal
    goal.current_amount += Decimal(str(amount))
    
    # Auto-complete if target reached
    if goal.current_amount >= goal.target_amount:
        goal.status = 'COMPLETED'
    
    db.commit()
    db.refresh(goal)
    
    return {
        "message": "Contribution added",
        "goal": goal,
        "progress": (goal.current_amount / goal.target_amount) * 100
    }

