"""OpenBanking Russia integration service."""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from app.models.user import User
from app.models.bank_connection import BankConnection, BankProvider, ConnectionStatus
from app.models.account import Account, AccountType, Currency
from app.integrations.vtb_api import OpenBankingClient
from app.utils.security import encrypt_token, decrypt_token


class OpenBankingService:
    """Service for OpenBanking Russia operations."""
    
    SUPPORTED_BANKS = ["vbank", "abank", "sbank"]
    
    @staticmethod
    async def get_bank_token(bank_code: str) -> str:
        """Get bank token for API access.
        
        This token is used for public API calls (products, etc.)
        Valid for 24 hours.
        
        Args:
            bank_code: Bank code (vbank, abank, sbank)
            
        Returns:
            Access token
        """
        async with OpenBankingClient(bank_code) as client:
            response = await client.get_bank_token()
            return response["access_token"]
    
    @staticmethod
    async def connect_bank_with_team_client(
        db: Session,
        user: User,
        bank_code: str,
        client_number: str = "1"
    ) -> BankConnection:
        """Connect bank using team075-X client.
        
        Connects with specified team client (team075-1 to team075-10).
        Each client has different profile (employee, VIP, entrepreneur, etc.)
        
        Args:
            db: Database session
            user: User object
            bank_code: Bank code (vbank, abank, sbank)
            client_number: Client number (1-10 for team075-1 to team075-10)
            
        Returns:
            Created BankConnection
        """
        if bank_code not in OpenBankingService.SUPPORTED_BANKS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported bank: {bank_code}"
            )
        
        # Validate client number
        if not client_number.isdigit() or not (1 <= int(client_number) <= 10):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client number must be between 1 and 10"
            )
        
        async with OpenBankingClient(bank_code, use_gost=user.use_gost_mode) as client:
            try:
                # 1. Determine which client to use
                # Check if this is a direct team client (team075-X format in email/login)
                if user.email.startswith("team075-") and user.email.count("-") == 1:
                    # Direct team client login - use their credentials
                    team_login = user.email.split("@")[0] if "@" in user.email else user.email
                    team_password = "1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di"
                elif client_number != "1":
                    # Demo user selecting specific client (1-10)
                    team_login = f"team075-{client_number}"
                    team_password = "1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di"
                else:
                    # Demo user with random client
                    demo_client = await client.get_random_demo_client()
                    team_login = demo_client["person_id"]
                    team_password = demo_client["password"]
                
                # 2. Login as that client
                login_response = await client.client_login(
                    team_login,
                    team_password
                )
                
                client_token = login_response["access_token"]
                
                # 3. Encrypt and store token
                encrypted_token = encrypt_token(client_token)
                
                # 4. Create bank connection
                bank_connection = BankConnection(
                    user_id=user.id,
                    bank_provider=BankProvider(bank_code),
                    bank_user_id=team_login,
                    access_token_encrypted=encrypted_token,
                    token_expires_at=datetime.utcnow() + timedelta(hours=24),
                    status=ConnectionStatus.ACTIVE
                )
                
                db.add(bank_connection)
                db.commit()
                db.refresh(bank_connection)
                
                # 5. Sync accounts
                await OpenBankingService._sync_accounts(
                    db, 
                    bank_connection, 
                    client_token,
                    bank_code
                )
                
                # 6. Sync transactions
                await OpenBankingService._sync_transactions(
                    db,
                    bank_connection,
                    client_token,
                    bank_code
                )
                
                return bank_connection
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"❌ ERROR connecting bank {bank_code}:")
                print(error_details)
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to connect bank: {str(e)}"
                )
    
    @staticmethod
    async def connect_bank_with_demo_client(
        db: Session,
        user: User,
        bank_code: str
    ) -> BankConnection:
        """Connect bank using random demo client (deprecated, use connect_bank_with_team_client instead)."""
        return await OpenBankingService.connect_bank_with_team_client(db, user, bank_code, "1")
    
    @staticmethod
    async def _sync_accounts(
        db: Session,
        bank_connection: BankConnection,
        client_token: str,
        bank_code: str
    ):
        """Sync accounts from bank."""
        async with OpenBankingClient(bank_code) as client:
            try:
                # Get accounts
                accounts_response = await client.get_accounts(client_token)
                # OpenBanking Russia format: data.account is the array
                accounts_data = accounts_response.get("data", {}).get("account", [])
                
                for acc_data in accounts_data:
                    # Get balance
                    try:
                        balance_response = await client.get_balances(
                            client_token,
                            acc_data["accountId"]
                        )
                        balance_data = balance_response.get("data", {}).get("balance", [{}])[0]
                        balance_amount = float(balance_data.get("amount", {}).get("amount", 0))
                        currency = balance_data.get("amount", {}).get("currency", "RUB")
                    except:
                        balance_amount = 0
                        currency = "RUB"
                    
                    # Check if account exists
                    existing = db.query(Account).filter(
                        Account.bank_connection_id == bank_connection.id,
                        Account.external_account_id == acc_data["accountId"]
                    ).first()
                    
                    if existing:
                        # Update
                        existing.balance = balance_amount
                        existing.currency = Currency(currency)
                        existing.last_synced_at = datetime.utcnow()
                    else:
                        # Create
                        account_type = acc_data.get("accountType", "Checking")
                        account_type_map = {
                            "Checking": AccountType.CHECKING,
                            "Business": AccountType.CHECKING,
                            "Savings": AccountType.SAVINGS,
                            "Deposit": AccountType.SAVINGS,
                            "Credit": AccountType.CREDIT,
                            "Loan": AccountType.LOAN,
                        }
                        
                        # Get first account identification
                        account_info = acc_data.get("account", [{}])[0] if acc_data.get("account") else {}
                        
                        new_account = Account(
                            bank_connection_id=bank_connection.id,
                            external_account_id=acc_data["accountId"],
                            account_number=account_info.get("identification", ""),
                            account_name=acc_data.get("nickname", acc_data.get("accountType", "Account")),
                            account_type=account_type_map.get(account_type, AccountType.CHECKING),
                            balance=balance_amount,
                            currency=Currency(currency),
                            last_synced_at=datetime.utcnow()
                        )
                        db.add(new_account)
                
                # Sync transactions for each account
                await OpenBankingService._sync_transactions(
                    db,
                    bank_connection,
                    client_token,
                    bank_code
                )
                
                bank_connection.last_synced_at = datetime.utcnow()
                bank_connection.status = ConnectionStatus.ACTIVE
                db.commit()
                
            except Exception as e:
                bank_connection.status = ConnectionStatus.ERROR
                bank_connection.error_message = str(e)
                db.commit()
                raise
    
    @staticmethod
    async def _sync_transactions(
        db: Session,
        bank_connection: BankConnection,
        client_token: str,
        bank_code: str
    ):
        """Sync transactions from bank accounts."""
        from app.models.transaction import Transaction, TransactionType
        from app.services.categorization_service import CategorizationService
        from datetime import timedelta
        
        async with OpenBankingClient(bank_code) as client:
            try:
                # Get all accounts for this connection
                accounts = db.query(Account).filter(
                    Account.bank_connection_id == bank_connection.id
                ).all()
                
                # Sync last 30 days of transactions
                from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
                
                for account in accounts:
                    try:
                        print(f"Syncing transactions for account {account.external_account_id}...")
                        tx_response = await client.get_transactions(
                            client_token,
                            account.external_account_id,
                            from_date=from_date
                        )
                        
                        # Parse transactions
                        tx_data = tx_response.get("data", {}).get("transaction", [])
                        print(f"Found {len(tx_data)} transactions for account {account.external_account_id}")
                        
                        for tx in tx_data:
                            # Check if transaction exists
                            tx_id = tx.get("transactionId")
                            existing = db.query(Transaction).filter(
                                Transaction.external_transaction_id == tx_id
                            ).first()
                            
                            if existing:
                                continue
                            
                            # Determine transaction type
                            amount_data = tx.get("amount", {})
                            amount = float(amount_data.get("amount", 0))
                            currency = amount_data.get("currency", "RUB")
                            credit_debit = tx.get("creditDebitIndicator", "Debit")
                            
                            tx_type = TransactionType.INCOME if credit_debit == "Credit" else TransactionType.EXPENSE
                            
                            # Auto-categorize
                            description = tx.get("transactionInformation", "Транзакция")
                            merchant = tx.get("merchantDetails", {}).get("merchantName") if tx.get("merchantDetails") else None
                            category_id = CategorizationService.categorize_transaction(db, description, merchant)
                            
                            # Create transaction
                            new_tx = Transaction(
                                account_id=account.id,
                                external_transaction_id=tx_id,
                                amount=abs(amount),
                                currency=currency,
                                transaction_type=tx_type,
                                transaction_date=datetime.fromisoformat(tx.get("bookingDateTime", tx.get("valueDateTime", datetime.utcnow().isoformat()))),
                                description=description,
                                merchant=merchant,
                                category_id=category_id
                            )
                            db.add(new_tx)
                            print(f"Added transaction: {description} - {amount} {currency}")
                    
                    except Exception as e:
                        print(f"Error syncing transactions for account {account.id}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                db.commit()
                
            except Exception as e:
                print(f"Error in _sync_transactions: {e}")
                # Don't fail the whole sync if transactions fail
                pass
    
    @staticmethod
    async def sync_transactions(
        db: Session,
        account: Account,
        bank_code: str
    ) -> int:
        """Sync transactions for an account.
        
        Returns:
            Number of new transactions synced
        """
        from app.models.transaction import Transaction, TransactionType
        
        # Get bank connection
        bank_connection = account.bank_connection
        client_token = decrypt_token(bank_connection.access_token_encrypted)
        
        async with OpenBankingClient(bank_code) as client:
            try:
                # Get transactions (last 30 days)
                from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
                
                trans_response = await client.get_transactions(
                    client_token,
                    account.external_account_id,
                    from_date=from_date
                )
                
                transactions_data = trans_response.get("data", {}).get("Transaction", [])
                new_count = 0
                
                for trans_data in transactions_data:
                    trans_id = trans_data.get("TransactionId", "")
                    
                    # Check if exists
                    existing = db.query(Transaction).filter(
                        Transaction.external_transaction_id == trans_id
                    ).first()
                    
                    if not existing:
                        amount_data = trans_data.get("Amount", {})
                        amount = float(amount_data.get("Amount", 0))
                        
                        # Determine type
                        credit_debit = trans_data.get("CreditDebitIndicator", "Debit")
                        trans_type = TransactionType.INCOME if credit_debit == "Credit" else TransactionType.EXPENSE
                        
                        new_trans = Transaction(
                            account_id=account.id,
                            external_transaction_id=trans_id,
                            amount=abs(amount),
                            transaction_type=trans_type,
                            description=trans_data.get("TransactionInformation", ""),
                            transaction_date=datetime.fromisoformat(
                                trans_data.get("BookingDateTime", datetime.utcnow().isoformat())
                            ),
                            is_pending=0
                        )
                        db.add(new_trans)
                        new_count += 1
                
                db.commit()
                return new_count
                
            except Exception as e:
                print(f"Failed to sync transactions: {e}")
                return 0
    
    @staticmethod
    async def get_bank_products(
        bank_code: str,
        product_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get products from bank catalog.
        
        Args:
            bank_code: Bank code
            product_type: Filter by type
            
        Returns:
            List of products
        """
        async with OpenBankingClient(bank_code) as client:
            # Get bank token
            bank_token = await OpenBankingService.get_bank_token(bank_code)
            
            # Get products
            products = await client.get_products(bank_token, product_type)
            
            return products

