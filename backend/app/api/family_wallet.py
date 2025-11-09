"""
Family Wallet - Create real shared family account in MyBank
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
import logging

from ..database import get_db
from ..models.user import User
from ..models.family import FamilyGroup, FamilyMember, FamilyRole
from ..api.auth import get_current_user
from ..integrations.mybank_client import get_mybank_client, DEFAULT_MYBANK_PASSWORD
import httpx

logger = logging.getLogger(__name__)

router = APIRouter()


class FamilyWalletCreate(BaseModel):
    """Create family wallet request"""
    name: Optional[str] = "Семейный счет"


class FamilyWalletResponse(BaseModel):
    """Family wallet response"""
    account_id: str
    account_number: str
    balance: Decimal
    family_id: int
    message: str


@router.post("/groups/{family_id}/wallet", response_model=FamilyWalletResponse)
async def create_family_wallet(
    family_id: int,
    data: FamilyWalletCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a real shared wallet in MyBank for the family.
    Only family admin can create the wallet.
    """
    # Check if user is admin
    member = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_id,
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.ADMIN
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only family admin can create wallet"
        )
    
    family = db.query(FamilyGroup).filter(FamilyGroup.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    
    try:
        # Create account in MyBank for family
        mybank = get_mybank_client()
        
        # Login as the admin user
        try:
            await mybank.login(current_user.email, DEFAULT_MYBANK_PASSWORD)
        except httpx.HTTPStatusError as login_err:
            logger.info(f"Login failed, trying to register: {login_err}")
            # If login fails, try to register
            try:
                await mybank.register_customer(
                    full_name=current_user.full_name or current_user.email.split('@')[0],
                    email=current_user.email,
                    phone=current_user.phone or "+70000000000",
                    password=DEFAULT_MYBANK_PASSWORD
                )
                logger.info(f"Successfully registered {current_user.email} in MyBank")
            except httpx.HTTPStatusError as reg_err:
                logger.error(f"Registration failed: {reg_err.response.status_code} - {reg_err.response.text}")
                if reg_err.response.status_code != 400:  # Not "already exists"
                    raise HTTPException(
                        status_code=500,
                        detail=f"Не удалось зарегистрироваться в MyBank: {reg_err.response.text}"
                    )
            # Try login again after registration
            try:
                await mybank.login(current_user.email, DEFAULT_MYBANK_PASSWORD)
            except httpx.HTTPStatusError as login_err2:
                logger.error(f"Login after registration failed: {login_err2}")
                raise HTTPException(
                    status_code=500,
                    detail="Не удалось войти в MyBank. Попробуйте создать цель сначала."
                )
        
        # Create a dedicated savings account for the family
        mybank_account = await mybank.create_account(
            account_type="savings",
            linked_goal_id=None
        )
        
        logger.info(f"✅ Family wallet created in MyBank: {mybank_account['account_id']} for family {family_id}")
        
        # Create Account record in FinanceHub DB for the family wallet
        from app.models.account import Account, AccountType
        from decimal import Decimal
        
        family_wallet_account = Account(
            bank_connection_id=None,  # No bank connection, this is a MyBank family wallet
            account_name=data.name or f"Семейный кошелек {family.name}",
            account_number=mybank_account["account_number"],
            account_type=AccountType.SAVINGS,
            balance=Decimal(str(mybank_account["balance"])),
            currency="RUB",
            is_active=1,
            external_account_id=mybank_account["account_id"],
            family_id=family_id,
        )
        db.add(family_wallet_account)
        db.commit()
        db.refresh(family_wallet_account)
        
        logger.info(f"✅ Family wallet Account created in FinanceHub: {family_wallet_account.id}")
        
        # Link wallet to family by storing in family metadata
        # We'll use FamilySharedAccount to link it
        from app.models.family import FamilySharedAccount
        
        # Get family creator as member
        family_creator_member = db.query(FamilyMember).filter(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id
        ).first()
        
        if family_creator_member:
            # Add wallet as shared account
            family_wallet_shared = FamilySharedAccount(
                family_id=family_id,
                member_id=family_creator_member.id,
                account_id=family_wallet_account.id
            )
            db.add(family_wallet_shared)
            db.commit()
            logger.info(f"✅ Family wallet added as shared account")
        
        return {
            "account_id": mybank_account["account_id"],
            "account_number": mybank_account["account_number"],
            "balance": mybank_account["balance"],
            "family_id": family_id,
            "financehub_account_id": family_wallet_account.id,
            "message": f"Семейный кошелек '{data.name}' успешно создан в MyBank и добавлен в семейные счета"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create family wallet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось создать семейный кошелек: {str(e)}"
        )


@router.post("/groups/{family_id}/wallet/fund")
async def fund_family_wallet(
    family_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fund the family wallet from personal card/account.
    """
    amount = data.get("amount")
    from_card_id = data.get("from_card_id")
    wallet_account_id = data.get("wallet_account_id")
    
    if not all([amount, wallet_account_id]):
        raise HTTPException(status_code=400, detail="amount and wallet_account_id required")
    
    # Check membership
    member = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_id,
        FamilyMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Not a family member")
    
    try:
        mybank = get_mybank_client()
        
        # Login
        await mybank.login(current_user.email, DEFAULT_MYBANK_PASSWORD)
        
        # Transfer to family wallet
        # (MyBank should support account-to-account transfers)
        result = await mybank.transfer(
            from_card_id=from_card_id,
            to_account_id=wallet_account_id,
            amount=Decimal(str(amount))
        )
        
        logger.info(f"✅ {current_user.email} funded family {family_id} wallet with {amount}")
        
        return {
            "success": True,
            "message": f"Переведено {amount} ₽ на семейный счет",
            "transaction_id": result.get("transaction_id")
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fund family wallet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось пополнить семейный счет: {str(e)}"
        )

