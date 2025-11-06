"""
Multibank Proxy API - межбанковское взаимодействие
Inspired by GalkinTech/bank-in-a-box
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..database import get_db
from ..models import User, BankConnection, Account, Transaction, Consent, ConsentScope
from ..utils.security import create_bank_token, verify_bank_token

router = APIRouter(prefix="/api/v1/multibank", tags=["Multibank"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class BankTokenRequest(BaseModel):
    bank_code: str
    purpose: str = "interbank"


class BankTokenResponse(BaseModel):
    token: str
    expires_in: int
    token_type: str = "Bearer"


class ConsentRequest(BaseModel):
    target_bank: str
    client_id: str  # ID клиента в целевом банке
    scopes: List[str] = ["accounts_read", "balances_read", "transactions_read"]
    duration_days: int = 90


class ConsentResponse(BaseModel):
    consent_id: str
    status: str
    valid_until: str
    scopes: List[str]


class AccountWithConsentRequest(BaseModel):
    target_bank: str
    consent_id: str
    client_id: str


class AccountInfo(BaseModel):
    account_id: str
    account_number: str
    currency: str
    account_type: str
    bank_code: str


class BalanceInfo(BaseModel):
    account_id: str
    available: float
    current: float
    currency: str


class TransactionWithConsentRequest(BaseModel):
    target_bank: str
    consent_id: str
    client_id: str
    account_id: Optional[str] = None
    limit: int = 100


class TransactionInfo(BaseModel):
    transaction_id: str
    account_id: str
    amount: float
    currency: str
    transaction_type: str
    description: Optional[str]
    transaction_date: str


class InterbankTransferRequest(BaseModel):
    from_bank: str
    from_account: str
    to_bank: str
    to_account: str
    amount: float
    currency: str = "RUB"
    description: Optional[str] = None
    consent_id: str


class InterbankTransferResponse(BaseModel):
    transfer_id: str
    status: str
    from_bank: str
    to_bank: str
    amount: float
    currency: str
    created_at: str


class BankStatistics(BaseModel):
    total_clients: int
    total_accounts: int
    total_balance: float
    total_transactions: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/bank-token", response_model=BankTokenResponse)
async def get_bank_token(
    request: BankTokenRequest,
    current_user: User = Depends(lambda: None),  # TODO: Add proper auth
    db: Session = Depends(get_db)
):
    """
    Получить RS256 токен банка для межбанковских операций
    
    Этот токен используется для запросов к другим банкам в мультибанковой сети.
    """
    try:
        # Создаем токен банка (RS256)
        token = create_bank_token(
            bank_code=request.bank_code,
            purpose=request.purpose
        )
        
        return BankTokenResponse(
            token=token,
            expires_in=3600,  # 1 час
            token_type="Bearer"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bank token: {str(e)}")


@router.post("/request-consent", response_model=ConsentResponse)
async def request_consent(
    request: ConsentRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Запросить согласие клиента другого банка на доступ к его данным
    
    Требует банковский токен в заголовке Authorization.
    """
    # Проверяем банковский токен
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bank token required")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Верифицируем токен банка
        payload = verify_bank_token(token)
        requesting_bank = payload.get("sub")
        
        # Создаем запрос на согласие
        # В реальном приложении это должно создать ConsentRequest в БД
        consent_id = f"consent-{requesting_bank}-{request.client_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        valid_until = datetime.now() + timedelta(days=request.duration_days)
        
        return ConsentResponse(
            consent_id=consent_id,
            status="pending",
            valid_until=valid_until.isoformat(),
            scopes=request.scopes
        )
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid bank token: {str(e)}")


@router.post("/accounts-with-consent", response_model=List[AccountInfo])
async def get_accounts_with_consent(
    request: AccountWithConsentRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Получить счета клиента другого банка используя consent
    
    Требует:
    - Банковский токен в Authorization
    - Действительный consent_id
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bank token required")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Верифицируем токен банка
        payload = verify_bank_token(token)
        requesting_bank = payload.get("sub")
        
        # Проверяем consent
        consent = db.query(Consent).filter(
            Consent.id == request.consent_id,
            Consent.status == "active"
        ).first()
        
        if not consent:
            raise HTTPException(status_code=403, detail="Invalid or expired consent")
        
        # Проверяем что consent разрешает чтение счетов
        if ConsentScope.ACCOUNTS_READ not in consent.scopes:
            raise HTTPException(status_code=403, detail="Consent does not allow reading accounts")
        
        # Получаем счета клиента
        accounts = db.query(Account).filter(
            Account.user_id == consent.user_id
        ).all()
        
        return [
            AccountInfo(
                account_id=str(acc.id),
                account_number=acc.account_number,
                currency=acc.currency,
                account_type=acc.account_type,
                bank_code=request.target_bank
            )
            for acc in accounts
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch accounts: {str(e)}")


@router.post("/balances-with-consent", response_model=List[BalanceInfo])
async def get_balances_with_consent(
    request: AccountWithConsentRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Получить балансы счетов клиента другого банка используя consent
    
    Требует:
    - Банковский токен в Authorization
    - Действительный consent_id
    - Scope: balances_read
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bank token required")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Верифицируем токен банка
        payload = verify_bank_token(token)
        requesting_bank = payload.get("sub")
        
        # Проверяем consent
        consent = db.query(Consent).filter(
            Consent.id == request.consent_id,
            Consent.status == "active"
        ).first()
        
        if not consent:
            raise HTTPException(status_code=403, detail="Invalid or expired consent")
        
        # Проверяем что consent разрешает чтение балансов
        if ConsentScope.BALANCES_READ not in consent.scopes:
            raise HTTPException(status_code=403, detail="Consent does not allow reading balances")
        
        # Получаем счета и их балансы
        accounts = db.query(Account).filter(
            Account.user_id == consent.user_id
        ).all()
        
        return [
            BalanceInfo(
                account_id=str(acc.id),
                available=float(acc.balance),
                current=float(acc.balance),
                currency=acc.currency
            )
            for acc in accounts
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch balances: {str(e)}")


@router.post("/transactions-with-consent", response_model=List[TransactionInfo])
async def get_transactions_with_consent(
    request: TransactionWithConsentRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Получить транзакции клиента другого банка используя consent
    
    Требует:
    - Банковский токен в Authorization
    - Действительный consent_id
    - Scope: transactions_read
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bank token required")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Верифицируем токен банка
        payload = verify_bank_token(token)
        requesting_bank = payload.get("sub")
        
        # Проверяем consent
        consent = db.query(Consent).filter(
            Consent.id == request.consent_id,
            Consent.status == "active"
        ).first()
        
        if not consent:
            raise HTTPException(status_code=403, detail="Invalid or expired consent")
        
        # Проверяем что consent разрешает чтение транзакций
        if ConsentScope.TRANSACTIONS_READ not in consent.scopes:
            raise HTTPException(status_code=403, detail="Consent does not allow reading transactions")
        
        # Получаем транзакции
        query = db.query(Transaction).join(Account).filter(
            Account.user_id == consent.user_id
        )
        
        if request.account_id:
            query = query.filter(Transaction.account_id == int(request.account_id))
        
        transactions = query.order_by(Transaction.transaction_date.desc()).limit(request.limit).all()
        
        return [
            TransactionInfo(
                transaction_id=str(tx.id),
                account_id=str(tx.account_id),
                amount=float(tx.amount),
                currency=tx.currency,
                transaction_type=tx.transaction_type,
                description=tx.description,
                transaction_date=tx.transaction_date.isoformat()
            )
            for tx in transactions
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")


@router.post("/interbank-transfer", response_model=InterbankTransferResponse)
async def create_interbank_transfer(
    request: InterbankTransferRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Создать межбанковский перевод
    
    Требует:
    - Банковский токен в Authorization
    - Действительный consent_id с scope payments_write
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bank token required")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Верифицируем токен банка
        payload = verify_bank_token(token)
        requesting_bank = payload.get("sub")
        
        # Проверяем consent
        consent = db.query(Consent).filter(
            Consent.id == request.consent_id,
            Consent.status == "active"
        ).first()
        
        if not consent:
            raise HTTPException(status_code=403, detail="Invalid or expired consent")
        
        # Проверяем что consent разрешает платежи
        if ConsentScope.PAYMENTS_WRITE not in consent.scopes:
            raise HTTPException(status_code=403, detail="Consent does not allow payments")
        
        # Создаем межбанковский перевод
        # В реальном приложении это должно создать Payment/InterbankTransfer в БД
        transfer_id = f"transfer-{request.from_bank}-{request.to_bank}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return InterbankTransferResponse(
            transfer_id=transfer_id,
            status="pending",
            from_bank=request.from_bank,
            to_bank=request.to_bank,
            amount=request.amount,
            currency=request.currency,
            created_at=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create transfer: {str(e)}")


@router.get("/bank-statistics", response_model=BankStatistics)
async def get_bank_statistics(
    bank_code: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Получить статистику банка
    
    Требует банковский токен в Authorization.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bank token required")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Верифицируем токен банка
        payload = verify_bank_token(token)
        
        # Получаем статистику
        connections = db.query(BankConnection).filter(
            BankConnection.bank_code == bank_code,
            BankConnection.status == "active"
        ).all()
        
        total_clients = len(set(conn.user_id for conn in connections))
        
        accounts = db.query(Account).join(BankConnection).filter(
            BankConnection.bank_code == bank_code
        ).all()
        
        total_accounts = len(accounts)
        total_balance = sum(float(acc.balance) for acc in accounts)
        
        transactions = db.query(Transaction).join(Account).join(BankConnection).filter(
            BankConnection.bank_code == bank_code
        ).count()
        
        return BankStatistics(
            total_clients=total_clients,
            total_accounts=total_accounts,
            total_balance=total_balance,
            total_transactions=transactions
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")

