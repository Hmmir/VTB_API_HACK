"""Bank connection endpoints - OpenBanking Russia integration."""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.bank_connection import BankConnectionResponse
from app.services.openbanking_service import OpenBankingService
from app.api.dependencies import get_current_user
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()


class ConnectBankRequest(BaseModel):
    """Request to connect a bank."""
    bank_code: str  # vbank, abank, or sbank


@router.post("/connect-demo", response_model=BankConnectionResponse, status_code=status.HTTP_201_CREATED)
async def connect_bank_demo(
    request: ConnectBankRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect a bank using demo client.
    
    Automatically creates connection with random test client from OpenBanking Sandbox.
    Supported banks: vbank, abank, sbank
    """
    connection = await OpenBankingService.connect_bank_with_demo_client(
        db, 
        current_user, 
        request.bank_code
    )
    return connection


@router.get("/connections", response_model=List[BankConnectionResponse])
def get_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bank connections for current user."""
    from app.models.bank_connection import BankConnection
    return db.query(BankConnection).filter(
        BankConnection.user_id == current_user.id
    ).all()


@router.post("/connections/{connection_id}/sync", response_model=BankConnectionResponse)
async def sync_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync a bank connection (refresh accounts and balances)."""
    from app.models.bank_connection import BankConnection
    from app.utils.security import decrypt_token
    
    # Get connection
    connection = db.query(BankConnection).filter(
        BankConnection.id == connection_id,
        BankConnection.user_id == current_user.id
    ).first()
    
    if not connection:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank connection not found"
        )
    
    # Decrypt token
    client_token = decrypt_token(connection.access_token_encrypted)
    
    # Sync accounts
    await OpenBankingService._sync_accounts(
        db, 
        connection, 
        client_token,
        connection.bank_provider.value
    )
    
    # Sync transactions
    await OpenBankingService._sync_transactions(
        db,
        connection,
        client_token,
        connection.bank_provider.value
    )
    
    db.refresh(connection)
    return connection


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a bank connection and all associated accounts."""
    from app.models.bank_connection import BankConnection
    from app.models.account import Account
    from fastapi import HTTPException
    
    # Get connection
    connection = db.query(BankConnection).filter(
        BankConnection.id == connection_id,
        BankConnection.user_id == current_user.id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank connection not found"
        )
    
    # Delete associated accounts
    db.query(Account).filter(Account.bank_connection_id == connection_id).delete()
    
    # Delete connection
    db.delete(connection)
    db.commit()


@router.get("/available-banks")
async def get_available_banks():
    """Get list of available banks in OpenBanking Russia Sandbox."""
    return {
        "banks": [
            {
                "code": "vbank",
                "name": "Virtual Bank",
                "description": "Виртуальный банк",
                "logo": "🏦"
            },
            {
                "code": "abank",
                "name": "Awesome Bank", 
                "description": "Потрясающий банк",
                "logo": "🏦"
            },
            {
                "code": "sbank",
                "name": "Smart Bank",
                "description": "Умный банк",
                "logo": "🏦"
            }
        ]
    }

