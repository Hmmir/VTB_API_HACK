"""MyBank integration endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any
from decimal import Decimal

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.bank_connection import BankConnection, BankProvider, ConnectionStatus
from app.models.account import Account, AccountType, Currency
from app.integrations.mybank_client import MyBankClient
from app.utils.security import encrypt_token, decrypt_token
from datetime import datetime, timedelta

router = APIRouter()


class MyBankConnectRequest(BaseModel):
    email: EmailStr
    password: str


class MyBankRegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str


class CardCreateRequest(BaseModel):
    card_type: str = "debit"  # debit or credit
    credit_limit: Decimal = Decimal("0")


@router.post("/connect")
async def connect_mybank(
    data: MyBankConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect existing MyBank account to FinanceHub"""
    
    try:
        async with MyBankClient() as client:
            # Get OAuth token
            token = await client.get_token(data.email, data.password)
            
            # Get customer info
            customer_info = await client.get_customer_info(token)
            
            # Check if connection already exists
            existing = db.query(BankConnection).filter(
                BankConnection.user_id == current_user.id,
                BankConnection.bank_provider == BankProvider.MYBANK
            ).first()
            
            if existing:
                # Update existing connection
                existing.access_token_encrypted = encrypt_token(token)
                existing.bank_user_id = customer_info["customer_id"]
                existing.status = ConnectionStatus.ACTIVE
                existing.token_expires_at = datetime.utcnow() + timedelta(minutes=30)
                existing.last_synced_at = datetime.utcnow()
                connection = existing
            else:
                # Create new connection
                connection = BankConnection(
                    user_id=current_user.id,
                    bank_provider=BankProvider.MYBANK,
                    bank_user_id=customer_info["customer_id"],
                    access_token_encrypted=encrypt_token(token),
                    status=ConnectionStatus.ACTIVE,
                    token_expires_at=datetime.utcnow() + timedelta(minutes=30),
                    last_synced_at=datetime.utcnow()
                )
                db.add(connection)
            
            db.commit()
            db.refresh(connection)
            
            # Sync accounts and cards
            await sync_mybank_data(connection, client, token, db)
            
            return {
                "success": True,
                "connection_id": connection.id,
                "bank": "mybank",
                "customer_id": customer_info["customer_id"]
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect MyBank: {str(e)}"
        )


@router.post("/register")
async def register_mybank(
    data: MyBankRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register new customer in MyBank and connect"""
    
    try:
        async with MyBankClient() as client:
            # Register customer
            customer = await client.register_customer(
                full_name=data.full_name,
                email=data.email,
                phone=data.phone,
                password=data.password
            )
            
            # Auto-connect after registration
            token = await client.get_token(data.email, data.password)
            
            # Create connection
            connection = BankConnection(
                user_id=current_user.id,
                bank_provider=BankProvider.MYBANK,
                bank_user_id=customer["customer_id"],
                access_token_encrypted=encrypt_token(token),
                status=ConnectionStatus.ACTIVE,
                token_expires_at=datetime.utcnow() + timedelta(minutes=30),
                last_synced_at=datetime.utcnow()
            )
            db.add(connection)
            db.commit()
            db.refresh(connection)
            
            # Sync accounts and cards (MyBank auto-creates defaults)
            await sync_mybank_data(connection, client, token, db)
            
            return {
                "success": True,
                "customer_id": customer["customer_id"],
                "email": customer["email"],
                "connection_id": connection.id
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to register in MyBank: {str(e)}"
        )


@router.post("/cards/create")
async def create_mybank_card(
    data: CardCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Issue new card in MyBank"""
    
    # Get MyBank connection
    connection = db.query(BankConnection).filter(
        BankConnection.user_id == current_user.id,
        BankConnection.bank_provider == BankProvider.MYBANK,
        BankConnection.status == ConnectionStatus.ACTIVE
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MyBank not connected"
        )
    
    try:
        token = decrypt_token(connection.access_token_encrypted)
        
        async with MyBankClient() as client:
            card = await client.create_card(
                token=token,
                card_type=data.card_type,
                credit_limit=data.credit_limit
            )
            
            # Create account record in our DB
            account = Account(
                bank_connection_id=connection.id,
                external_account_id=card["card_id"],
                account_number=card["card_number"],
                account_name=f"MyBank {card['card_type'].title()} Card",
                account_type=AccountType.CHECKING if data.card_type == "debit" else AccountType.CREDIT,
                balance=Decimal(str(card["balance"])),
                currency=Currency.RUB,
                credit_limit=Decimal(str(card.get("credit_limit", 0))) if data.card_type == "credit" else None,
                is_active=1,
                last_synced_at=datetime.utcnow()
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            
            return {
                "success": True,
                "card": card,
                "account_id": account.id
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create card: {str(e)}"
        )


@router.post("/sync")
async def sync_mybank(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually sync MyBank data"""
    
    connection = db.query(BankConnection).filter(
        BankConnection.user_id == current_user.id,
        BankConnection.bank_provider == BankProvider.MYBANK,
        BankConnection.status == ConnectionStatus.ACTIVE
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MyBank not connected"
        )
    
    try:
        token = decrypt_token(connection.access_token_encrypted)
        async with MyBankClient() as client:
            await sync_mybank_data(connection, client, token, db)
        
        return {"success": True, "message": "MyBank data synced"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sync failed: {str(e)}"
        )


async def sync_mybank_data(
    connection: BankConnection,
    client: MyBankClient,
    token: str,
    db: Session
):
    """Sync accounts and cards from MyBank"""
    
    # Get accounts
    accounts_data = await client.get_accounts(token)
    
    for acc_data in accounts_data:
        # Check if account exists
        existing = db.query(Account).filter(
            Account.bank_connection_id == connection.id,
            Account.external_account_id == acc_data["account_id"]
        ).first()
        
        if existing:
            # Update balance
            existing.balance = Decimal(str(acc_data["balance"]))
            existing.last_synced_at = datetime.utcnow()
        else:
            # Create new account
            account = Account(
                bank_connection_id=connection.id,
                external_account_id=acc_data["account_id"],
                account_number=acc_data["account_number"],
                account_name=f"MyBank {acc_data['account_type'].title()} Account",
                account_type=AccountType.CHECKING if acc_data["account_type"] == "checking" else AccountType.SAVINGS,
                balance=Decimal(str(acc_data["balance"])),
                currency=Currency.RUB,
                is_active=1 if acc_data["status"] == "active" else 0,
                last_synced_at=datetime.utcnow()
            )
            db.add(account)
    
    # Get cards
    cards_data = await client.get_cards(token)
    
    for card_data in cards_data:
        # Check if card exists (stored as account)
        existing = db.query(Account).filter(
            Account.bank_connection_id == connection.id,
            Account.external_account_id == card_data["card_id"]
        ).first()
        
        if existing:
            # Update balance
            existing.balance = Decimal(str(card_data["balance"]))
            existing.last_synced_at = datetime.utcnow()
        else:
            # Create new card (as account)
            account = Account(
                bank_connection_id=connection.id,
                external_account_id=card_data["card_id"],
                account_number=card_data["card_number"],
                account_name=f"MyBank {card_data['card_type'].title()} Card",
                account_type=AccountType.CHECKING if card_data["card_type"] == "debit" else AccountType.CREDIT,
                balance=Decimal(str(card_data["balance"])),
                currency=Currency.RUB,
                credit_limit=Decimal(str(card_data.get("credit_limit", 0))) if card_data["card_type"] == "credit" else None,
                is_active=1 if card_data["status"] == "active" else 0,
                last_synced_at=datetime.utcnow()
            )
            db.add(account)
    
    db.commit()
    connection.last_synced_at = datetime.utcnow()
    db.commit()


__all__ = ["router"]

