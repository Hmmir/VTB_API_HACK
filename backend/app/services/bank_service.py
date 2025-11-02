"""Bank connection service."""
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.bank_connection import BankConnection, BankProvider, ConnectionStatus
from app.models.account import Account, AccountType, Currency
from app.schemas.bank_connection import BankConnectionCreate, BankConnectionResponse
from app.integrations.vtb_api import VTBAPIClient
from app.utils.security import encrypt_token, decrypt_token


class BankService:
    """Service for bank connection operations."""
    
    @staticmethod
    async def connect_bank(
        db: Session,
        user: User,
        connection_data: BankConnectionCreate
    ) -> BankConnection:
        """Connect a bank account via OAuth."""
        async with VTBAPIClient() as api_client:
            # Exchange authorization code for tokens
            token_response = await api_client.exchange_code_for_token(
                connection_data.bank_provider,
                connection_data.authorization_code
            )
            
            # Encrypt tokens before storing
            access_token_encrypted = encrypt_token(token_response["access_token"])
            refresh_token_encrypted = None
            if "refresh_token" in token_response:
                refresh_token_encrypted = encrypt_token(token_response["refresh_token"])
            
            # Calculate token expiration
            token_expires_at = None
            if "expires_in" in token_response:
                from datetime import timedelta
                token_expires_at = datetime.utcnow() + timedelta(seconds=token_response["expires_in"])
            
            # Create bank connection
            bank_connection = BankConnection(
                user_id=user.id,
                bank_provider=BankProvider(connection_data.bank_provider),
                bank_user_id=token_response.get("user_id", "unknown"),
                access_token_encrypted=access_token_encrypted,
                refresh_token_encrypted=refresh_token_encrypted,
                token_expires_at=token_expires_at,
                status=ConnectionStatus.ACTIVE
            )
            
            db.add(bank_connection)
            db.commit()
            db.refresh(bank_connection)
            
            # Fetch and sync accounts
            await BankService._sync_accounts(db, bank_connection, token_response["access_token"])
            
            return bank_connection
    
    @staticmethod
    async def _sync_accounts(
        db: Session,
        bank_connection: BankConnection,
        access_token: str
    ):
        """Sync accounts from bank."""
        async with VTBAPIClient() as api_client:
            try:
                # Fetch accounts from bank
                accounts_response = await api_client.get_accounts(
                    access_token,
                    bank_connection.bank_provider.value
                )
                
                # Process each account
                for account_data in accounts_response.get("accounts", []):
                    # Check if account already exists
                    existing_account = db.query(Account).filter(
                        Account.bank_connection_id == bank_connection.id,
                        Account.external_account_id == account_data["id"]
                    ).first()
                    
                    if existing_account:
                        # Update existing account
                        existing_account.balance = account_data.get("balance", 0)
                        existing_account.last_synced_at = datetime.utcnow()
                    else:
                        # Create new account
                        new_account = Account(
                            bank_connection_id=bank_connection.id,
                            external_account_id=account_data["id"],
                            account_number=account_data.get("account_number"),
                            account_name=account_data.get("name", "Account"),
                            account_type=AccountType(account_data.get("type", "checking")),
                            balance=account_data.get("balance", 0),
                            currency=Currency(account_data.get("currency", "RUB")),
                            credit_limit=account_data.get("credit_limit"),
                            last_synced_at=datetime.utcnow()
                        )
                        db.add(new_account)
                
                # Update bank connection sync time
                bank_connection.last_synced_at = datetime.utcnow()
                db.commit()
                
            except Exception as e:
                bank_connection.status = ConnectionStatus.ERROR
                bank_connection.error_message = str(e)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to sync accounts: {str(e)}"
                )
    
    @staticmethod
    def get_user_connections(db: Session, user: User) -> List[BankConnection]:
        """Get all bank connections for user."""
        return db.query(BankConnection).filter(
            BankConnection.user_id == user.id
        ).all()
    
    @staticmethod
    async def sync_connection(
        db: Session,
        user: User,
        connection_id: int
    ) -> BankConnection:
        """Sync a bank connection (refresh data)."""
        # Get connection
        connection = db.query(BankConnection).filter(
            BankConnection.id == connection_id,
            BankConnection.user_id == user.id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank connection not found"
            )
        
        # Decrypt access token
        access_token = decrypt_token(connection.access_token_encrypted)
        
        # Sync accounts
        await BankService._sync_accounts(db, connection, access_token)
        
        return connection

