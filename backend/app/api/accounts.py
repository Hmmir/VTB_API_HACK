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
    accounts = db.query(Account).join(Account.bank_connection).filter(
        Account.bank_connection.has(user_id=current_user.id)
    ).all()
    return accounts


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

        debit_transaction = Transaction(
            account_id=source_account.id,
            category_id=None,
            external_transaction_id=f"transfer-{transfer_id}-debit",
            amount=-amount,
            currency=source_account.currency.value if hasattr(source_account.currency, "value") else source_account.currency,
            transaction_type=TransactionType.TRANSFER,
            description=transfer.description or f"Перевод на счет {destination_account.account_name}",
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
            description=transfer.description or f"Перевод со счета {source_account.account_name}",
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

