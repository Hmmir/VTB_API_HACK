"""Account endpoints."""
from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.account import AccountResponse, AccountTransferRequest, AccountTransferResponse

router = APIRouter()


@router.get("/", response_model=List[AccountResponse])
def get_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all accounts for current user."""
    from sqlalchemy import or_, and_
    from app.models.goal import Goal
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Получаем имена MyBank счетов для целей пользователя
    user_goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    mybank_goal_account_names = [f"MyBank Goal: {goal.name}" for goal in user_goals]
    
    logger.info(f"User {current_user.id} has {len(user_goals)} goals, MyBank goal account names: {mybank_goal_account_names}")
    
    # Получаем семейные MyBank кошельки пользователя
    from app.models.family import FamilySharedAccount, FamilyMember
    
    # Находим все семьи где пользователь участник
    user_member_ids = db.query(FamilyMember.id).filter(FamilyMember.user_id == current_user.id).all()
    user_member_ids = [m[0] for m in user_member_ids]
    
    # Находим ID всех семейных счетов
    family_shared_account_ids = []
    if user_member_ids:
        family_shared_account_ids = db.query(FamilySharedAccount.account_id).filter(
            FamilySharedAccount.member_id.in_(user_member_ids)
        ).all()
        family_shared_account_ids = [a[0] for a in family_shared_account_ids]
    
    logger.info(f"User {current_user.id} has {len(family_shared_account_ids)} family shared accounts")
    
    # Получаем счета с подключениями, MyBank счета целей И семейные MyBank счета
    query_filter = Account.bank_connection.has(user_id=current_user.id)
    
    # Добавляем MyBank счета целей
    if mybank_goal_account_names:
        query_filter = or_(
            query_filter,
            and_(
                Account.bank_connection_id.is_(None),
                Account.account_name.in_(mybank_goal_account_names)
            )
        )
    
    # Добавляем семейные счета (они тоже MyBank без подключения)
    if family_shared_account_ids:
        query_filter = or_(
            query_filter,
            Account.id.in_(family_shared_account_ids)
        )
    
    accounts = db.query(Account).outerjoin(Account.bank_connection).filter(query_filter).all()
    
    logger.info(f"Found {len(accounts)} accounts for user {current_user.id}")
    
    # Добавляем информацию о банке к каждому счету
    result = []
    for account in accounts:
        # Определяем название банка по provider
        bank_name_map = {
            "vbank": "VBank",
            "abank": "ABank",
            "sbank": "SBank",
            "mybank": "MyBank"
        }
        
        # Если нет подключения, это MyBank счет цели
        if not account.bank_connection:
            provider = "mybank"
            bank_display_name = "MyBank"
            logger.info(f"MyBank account without connection: {account.account_name}")
        else:
            provider = account.bank_connection.bank_provider.value
            bank_display_name = bank_name_map.get(provider, provider.upper() if provider else "Банк")
        
        account_dict = {
            "id": account.id,
            "bank_connection_id": account.bank_connection_id,
            "account_name": account.account_name,
            "account_number": account.account_number,
            "account_type": account.account_type,
            "balance": account.balance,
            "currency": account.currency,
            "credit_limit": account.credit_limit,
            "is_active": account.is_active,
            "last_synced_at": account.last_synced_at,
            "bank_name": bank_display_name,
            "bank_provider": provider,
        }
        result.append(account_dict)
    
    return result


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific account details."""
    account = db.query(Account).join(Account.bank_connection).filter(
        Account.id == account_id,
        Account.bank_connection.has(user_id=current_user.id)
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return account


@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific account."""
    account = db.query(Account).join(Account.bank_connection).filter(
        Account.id == account_id,
        Account.bank_connection.has(user_id=current_user.id)
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    db.query(Transaction).filter(Transaction.account_id == account_id).delete()
    db.delete(account)
    db.commit()

    return {"message": "Account deleted successfully"}


@router.post("/transfer", response_model=AccountTransferResponse, status_code=status.HTTP_201_CREATED)
def transfer_between_accounts(
    transfer: AccountTransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Transfer funds between two user accounts."""

    if transfer.from_account_id == transfer.to_account_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Укажите разные счета для перевода")

    amount: Decimal = transfer.amount

    source_account = db.query(Account).join(Account.bank_connection).filter(
        Account.id == transfer.from_account_id,
        Account.bank_connection.has(user_id=current_user.id)
    ).first()

    destination_account = db.query(Account).join(Account.bank_connection).filter(
        Account.id == transfer.to_account_id,
        Account.bank_connection.has(user_id=current_user.id)
    ).first()

    if not source_account or not destination_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счета не найдены или недоступны")

    if source_account.currency != destination_account.currency:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Переводы между разными валютами пока не поддерживаются")

    if source_account.balance < amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недостаточно средств на счете отправителя")

    now = datetime.utcnow()
    transfer_id = uuid4().hex

    try:
        source_account.balance = source_account.balance - amount
        destination_account.balance = destination_account.balance + amount

        # Создаем читаемые имена счетов
        dest_name = destination_account.account_name or f"счет {destination_account.id}"
        src_name = source_account.account_name or f"счет {source_account.id}"
        
        debit_transaction = Transaction(
            account_id=source_account.id,
            category_id=None,
            external_transaction_id=f"transfer-{transfer_id}-debit",
            amount=-amount,
            currency=source_account.currency.value if hasattr(source_account.currency, "value") else source_account.currency,
            transaction_type=TransactionType.TRANSFER,
            description=transfer.description or f"Перевод на {dest_name}",
            merchant=None,
            transaction_date=now,
            is_pending=0
        )

        credit_transaction = Transaction(
            account_id=destination_account.id,
            category_id=None,
            external_transaction_id=f"transfer-{transfer_id}-credit",
            amount=amount,
            currency=destination_account.currency.value if hasattr(destination_account.currency, "value") else destination_account.currency,
            transaction_type=TransactionType.TRANSFER,
            description=transfer.description or f"Перевод с {src_name}",
            merchant=None,
            transaction_date=now,
            is_pending=0
        )

        db.add(debit_transaction)
        db.add(credit_transaction)
        db.commit()
        db.refresh(debit_transaction)
        db.refresh(credit_transaction)

        return AccountTransferResponse(
            transaction_id=debit_transaction.id,
            mirror_transaction_id=credit_transaction.id,
            message="Перевод выполнен"
        )
    except Exception as exc:  # pragma: no cover
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось выполнить перевод") from exc


@router.get("/{account_id}/transactions")
def get_account_transactions(
    account_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transactions for a specific account."""
    # Проверяем что счет принадлежит пользователю или доступен через семейную группу
    from sqlalchemy import or_, and_
    from app.models.bank_connection import BankConnection
    from app.models.family import FamilySharedAccount, FamilyMember

    user_member_records = db.query(FamilyMember.id, FamilyMember.family_id).filter(
        FamilyMember.user_id == current_user.id
    ).all()
    user_member_ids = [record[0] for record in user_member_records]
    user_family_ids = [record[1] for record in user_member_records]

    access_conditions = [BankConnection.user_id == current_user.id]
    if user_family_ids:
        access_conditions.append(
            and_(
                Account.bank_connection_id.is_(None),
                Account.family_id.isnot(None),
                Account.family_id.in_(user_family_ids),
            )
        )

    account = db.query(Account).outerjoin(
        BankConnection, Account.bank_connection_id == BankConnection.id
    ).filter(
        Account.id == account_id,
        or_(*access_conditions)
    ).first()
    
    # Проверка 2: Счет доступен через семейную группу (shared accounts)
    if not account and user_member_ids:
        family_account = db.query(FamilySharedAccount).filter(
            FamilySharedAccount.account_id == account_id,
            FamilySharedAccount.member_id.in_(user_member_ids)
        ).first()

        if family_account:
            account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or access denied"
        )
    
    # Получаем транзакции
    transactions = db.query(Transaction).filter(
        Transaction.account_id == account_id
    ).order_by(
        Transaction.transaction_date.desc()
    ).limit(limit).all()
    
    return transactions

