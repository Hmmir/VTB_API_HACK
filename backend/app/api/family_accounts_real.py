"""
Family Accounts with Real Money (MyBank Integration)
Управление семейными счетами с реальными операциями через MyBank
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models.user import User
from ..models.family import (
    FamilyGroup, FamilyMember, FamilyGoal, FamilyGoalContribution,
    FamilyRole, FamilyMemberStatus, FamilyGoalStatus
)
from ..models.account import Account
from ..api.auth import get_current_user
from ..integrations.mybank_client import get_mybank_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Schemas
class FamilyAccountCreate(BaseModel):
    """Create family shared account"""
    account_type: str = "savings"  # savings, checking
    initial_funding: Optional[Decimal] = Decimal("0")


class FamilyAccountResponse(BaseModel):
    account_id: str
    account_number: str
    balance: Decimal
    currency: str
    family_id: int
    
    class Config:
        from_attributes = True


class MemberCardSelect(BaseModel):
    """Member selects which cards to share with family"""
    card_ids: List[str]


class GoalWithAccountCreate(BaseModel):
    """Create goal with dedicated MyBank account"""
    name: str
    description: Optional[str]
    target_amount: Decimal
    deadline: Optional[datetime]


class GoalContributionRequest(BaseModel):
    """Contribute to goal from personal card"""
    amount: Decimal
    source_card_id: Optional[str]  # If None, use default account


# Endpoints
@router.post("/groups/{family_id}/accounts", response_model=FamilyAccountResponse)
async def create_family_account(
    family_id: int,
    data: FamilyAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create shared family account via MyBank
    Only admin can create family accounts
    """
    # Check membership and role
    member = db.query(FamilyMember).filter(
        and_(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id,
            FamilyMember.role == FamilyRole.ADMIN
        )
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only family admin can create shared accounts"
        )
    
    family = db.query(FamilyGroup).filter(FamilyGroup.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    
    try:
        # Create account in MyBank
        mybank = get_mybank_client()
        # TODO: Authenticate with MyBank using family's credentials
        # For now, create account directly
        
        mybank_account = await mybank.create_account(
            account_type=data.account_type,
            linked_goal_id=None
        )
        
        # Store reference in our DB
        account = Account(
            user_id=current_user.id,  # Created by admin
            bank_connection_id=None,  # Direct MyBank connection
            account_number=mybank_account["account_number"],
            account_name=f"{family.name} - Family Account",
            account_type=data.account_type,
            balance=mybank_account["balance"],
            currency=mybank_account["currency"],
            status="active",
            bank_product_id=mybank_account["account_id"],
            family_id=family_id
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        
        logger.info(f"Created family account {account.id} for family {family_id}")
        
        return {
            "account_id": mybank_account["account_id"],
            "account_number": account.account_number,
            "balance": account.balance,
            "currency": account.currency,
            "family_id": family_id
        }
        
    except Exception as e:
        logger.error(f"Failed to create family account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create family account: {str(e)}"
        )


@router.post("/groups/{family_id}/members/me/cards")
async def link_member_cards(
    family_id: int,
    data: MemberCardSelect,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Link member's personal cards to family group
    Called when user joins family to select which cards to share
    """
    member = db.query(FamilyMember).filter(
        and_(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id
        )
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Not a family member")
    
    # TODO: Store card_ids in family_member_accounts table
    # For now, just validate cards exist in user's MyBank account
    
    try:
        mybank = get_mybank_client()
        # Authenticate as user
        cards = await mybank.get_cards()
        
        # Validate requested cards belong to user
        available_card_ids = [card["card_id"] for card in cards]
        for card_id in data.card_ids:
            if card_id not in available_card_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Card {card_id} not found or doesn't belong to you"
                )
        
        # Store selection (simplified - in real app, use family_member_accounts table)
        logger.info(f"User {current_user.id} linked {len(data.card_ids)} cards to family {family_id}")
        
        return {
            "success": True,
            "linked_cards": len(data.card_ids),
            "message": "Cards linked to family group"
        }
        
    except Exception as e:
        logger.error(f"Failed to link cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{family_id}/goals", response_model=dict)
async def create_family_goal_with_account(
    family_id: int,
    data: GoalWithAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create family goal with dedicated MyBank account
    Money is actually stored in MyBank, not just tracked
    """
    # Verify membership
    member = db.query(FamilyMember).filter(
        and_(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id,
            FamilyMember.status == FamilyMemberStatus.ACTIVE
        )
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Not an active family member")
    
    try:
        # Create goal with dedicated account in MyBank
        mybank = get_mybank_client()
        mybank_goal = await mybank.create_goal(
            name=data.name,
            target_amount=data.target_amount,
            deadline=data.deadline
        )
        
        # Store in our DB
        goal = FamilyGoal(
            family_id=family_id,
            name=data.name,
            description=data.description,
            target_amount=data.target_amount,
            current_amount=Decimal("0"),
            deadline=data.deadline,
            status=FamilyGoalStatus.ACTIVE,
            created_by=current_user.id,
            external_goal_id=mybank_goal["goal_id"],
            linked_account_id=None  # We can link later if needed
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        
        logger.info(f"Created family goal {goal.id} with MyBank account {mybank_goal['account_id']}")
        
        return {
            "id": goal.id,
            "name": goal.name,
            "target_amount": float(goal.target_amount),
            "current_amount": float(goal.current_amount),
            "external_goal_id": mybank_goal["goal_id"],
            "external_account_id": mybank_goal["account_id"],
            "progress": 0,
            "status": goal.status
        }
        
    except Exception as e:
        logger.error(f"Failed to create goal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{family_id}/goals/{goal_id}/contribute")
async def contribute_to_family_goal(
    family_id: int,
    goal_id: int,
    data: GoalContributionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Contribute to family goal from personal card
    Real money transfer via MyBank
    """
    # Verify membership
    member = db.query(FamilyMember).filter(
        and_(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id,
            FamilyMember.status == FamilyMemberStatus.ACTIVE
        )
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Not an active family member")
    
    # Get goal
    goal = db.query(FamilyGoal).filter(
        and_(
            FamilyGoal.id == goal_id,
            FamilyGoal.family_id == family_id
        )
    ).first()
    
    if not goal or not goal.external_goal_id:
        raise HTTPException(status_code=404, detail="Goal not found or not linked to MyBank")
    
    try:
        # Contribute via MyBank
        mybank = get_mybank_client()
        result = await mybank.contribute_to_goal(
            goal_id=goal.external_goal_id,
            amount=data.amount,
            from_card_id=data.source_card_id
        )
        
        # Update local DB
        goal.current_amount += data.amount
        if goal.current_amount >= goal.target_amount:
            goal.status = FamilyGoalStatus.COMPLETED
            goal.completed_at = datetime.utcnow()
        
        # Record contribution
        contribution = FamilyGoalContribution(
            goal_id=goal.id,
            member_id=member.id,
            amount=data.amount,
            source_account_id=None,  # Could link to Account if we track cards
            external_tx_id=result.get("transaction_id")
        )
        db.add(contribution)
        
        # Создаем транзакцию для отображения в личной истории (как в личных целях)
        # Это позволяет видеть взнос в разделе "Транзакции"
        if data.source_card_id:
            from app.models.transaction import Transaction, TransactionType
            import uuid
            
            # Находим счет-источник
            source_account = db.query(Account).filter(
                Account.id == data.source_card_id,
                Account.bank_connection.has(user_id=current_user.id)
            ).first()
            
            if source_account:
                # Списываем деньги со счета
                source_account.balance -= data.amount
                db.add(source_account)
                
                # Создаем транзакцию для истории
                transaction = Transaction(
                    account_id=source_account.id,
                    external_transaction_id=f"FAMILY_GOAL_{uuid.uuid4().hex[:16].upper()}",
                    amount=-data.amount,  # Отрицательная сумма = расход
                    description=f"Взнос на семейную цель: {goal.name}",
                    transaction_date=datetime.utcnow(),
                    category_id=None,  # Без категории (будет показано отдельно)
                    transaction_type=TransactionType.EXPENSE
                )
                db.add(transaction)
                logger.info(f"Created transaction for family goal contribution: {transaction.external_transaction_id}")
        
        db.commit()
        
        logger.info(f"User {current_user.id} contributed {data.amount} to goal {goal_id}")
        
        return {
            "success": True,
            "goal_id": goal.id,
            "contributed": float(data.amount),
            "current_amount": float(goal.current_amount),
            "target_amount": float(goal.target_amount),
            "progress": float((goal.current_amount / goal.target_amount) * 100) if goal.target_amount > 0 else 0,
            "status": goal.status
        }
        
    except Exception as e:
        logger.error(f"Failed to contribute: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{family_id}/accounts")
async def get_family_accounts(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all family shared accounts"""
    # Verify membership
    member = db.query(FamilyMember).filter(
        and_(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id
        )
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Not a family member")
    
    accounts = db.query(Account).filter(Account.family_id == family_id).all()
    
    return [
        {
            "id": acc.id,
            "account_number": acc.account_number,
            "account_name": acc.account_name,
            "balance": float(acc.balance),
            "currency": acc.currency,
            "status": acc.status,
            "external_id": acc.bank_product_id
        }
        for acc in accounts
    ]
