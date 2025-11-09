"""Family shared account creation through Banking API."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.bank_connection import BankConnection
from app.services.bank_service import BankService

router = APIRouter(prefix="/family", tags=["Family Shared Accounts"])


class CreateFamilyAccountRequest(BaseModel):
    """Request for creating family shared account."""
    family_id: int
    account_name: str
    currency: str = "RUB"
    bank_code: str  # Which bank to create account in


@router.post("/shared-account/create", status_code=status.HTTP_201_CREATED)
async def create_family_shared_account(
    data: CreateFamilyAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a shared family account through Banking API.
    
    This endpoint creates a new bank account that can be shared among family members.
    
    According to open.bankingapi.ru documentation:
    POST /api/v1/accounts
    {
        "account_type": "shared",
        "currency": "RUB",
        "name": "Семейный счет",
        "authorized_users": [user_id_1, user_id_2]
    }
    """
    try:
        # TODO: Get family members to add as authorized users
        from app.services.family_service import FamilyService
        from app.models.family import FamilyMember
        
        # Verify user is admin of the family
        if not FamilyService.is_admin(db, data.family_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only family admin can create shared account"
            )
        
        # Get all active family members
        members = db.query(FamilyMember).filter(
            FamilyMember.family_id == data.family_id,
            FamilyMember.status == "active"
        ).all()
        
        authorized_user_ids = [m.user_id for m in members]
        
        # Create account through Banking API
        # According to open.bankingapi.ru "Свой банк" section
        from app.integrations.vtb_api import VTBAPIClient
        from app.models.account import Account, AccountType, Currency as CurrencyEnum
        
        # Get bank connection for creating user
        bank_connection = db.query(BankConnection).filter(
            BankConnection.user_id == current_user.id,
            BankConnection.status == "active"
        ).first()
        
        if not bank_connection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must have at least one active bank connection to create family account"
            )
        
        # Prepare API request for shared account creation
        account_creation_data = {
            "account_type": "shared",
            "currency": data.currency,
            "name": data.account_name,
            "authorized_users": authorized_user_ids,
            "metadata": {
                "family_id": data.family_id,
                "created_by": current_user.id,
                "is_family_account": True
            }
        }
        
        async with VTBAPIClient() as api_client:
            try:
                # Decrypt access token
                from app.utils.security import decrypt_token
                access_token = decrypt_token(bank_connection.access_token_encrypted)
                
                # Call Banking API to create shared account
                created_account = await api_client.create_shared_account(
                    access_token,
                    data.bank_code,
                    account_creation_data
                )
                
                # Save account to our database
                new_account = Account(
                    bank_connection_id=bank_connection.id,
                    external_account_id=created_account.get("id"),
                    account_number=created_account.get("account_number"),
                    account_name=data.account_name,
                    account_type=AccountType.SHARED,
                    balance=0.0,
                    currency=CurrencyEnum[data.currency],
                    is_family_account=True,
                    family_id=data.family_id
                )
                db.add(new_account)
                
                # Link account to all family members
                from app.models.family import FamilySharedAccount, AccountVisibility
                for member in members:
                    shared_link = FamilySharedAccount(
                        family_id=data.family_id,
                        member_id=member.id,
                        account_id=new_account.id,
                        visibility=AccountVisibility.FAMILY
                    )
                    db.add(shared_link)
                
                db.commit()
                db.refresh(new_account)
                
                return {
                    "message": "Family shared account created successfully",
                    "account_id": new_account.id,
                    "account_number": new_account.account_number,
                    "account_name": data.account_name,
                    "authorized_users_count": len(authorized_user_ids),
                    "balance": 0.0,
                    "currency": data.currency
                }
                
            except Exception as api_error:
                # If Banking API fails, log and return error
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Banking API error: {str(api_error)}"
                )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create family account: {str(e)}"
        )

