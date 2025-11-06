"""Payment orchestration service."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.account import Account, Currency
from app.models.consent import Consent, ConsentStatus, PartnerBank, ConsentScope
from app.models.payment import Payment, PaymentType, PaymentStatus, InterbankTransfer, InterbankTransferStatus
from app.models.transaction import Transaction, TransactionType


class PaymentService:
    """Service for payment processing and interbank transfers."""

    @staticmethod
    def _validate_currency(account: Account, currency: Currency) -> None:
        """Ensure currency matches account currency."""
        if account.currency != currency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Currency mismatch: account uses {account.currency.value}, but {currency.value} provided"
            )

    @staticmethod
    def _validate_balance(account: Account, amount: Decimal) -> None:
        """Ensure sufficient balance."""
        if account.balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient funds: balance {account.balance}, required {amount}"
            )

    @staticmethod
    def process_internal_transfer(
        db: Session,
        *,
        user_id: int,
        from_account_id: int,
        to_account_id: int,
        amount: Decimal,
        description: Optional[str]
    ) -> Payment:
        """Process transfer between user's own accounts (improved version)."""
        if from_account_id == to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and destination accounts must be different"
            )

        # Fetch accounts with lock
        from_account = (
            db.query(Account)
            .join(Account.bank_connection)
            .filter(
                Account.id == from_account_id,
                Account.bank_connection.has(user_id=user_id)
            )
            .with_for_update()
            .first()
        )

        to_account = (
            db.query(Account)
            .join(Account.bank_connection)
            .filter(
                Account.id == to_account_id,
                Account.bank_connection.has(user_id=user_id)
            )
            .with_for_update()
            .first()
        )

        if not from_account or not to_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both accounts not found"
            )

        PaymentService._validate_currency(from_account, from_account.currency)
        PaymentService._validate_currency(to_account, to_account.currency)

        if from_account.currency != to_account.currency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cross-currency transfers not supported yet"
            )

        PaymentService._validate_balance(from_account, amount)

        # Create payment record
        payment = Payment(
            user_id=user_id,
            account_id=from_account_id,
            amount=amount,
            currency=from_account.currency,
            counterparty=to_account.account_name,
            description=description or f"Transfer to {to_account.account_name}",
            payment_type=PaymentType.INTERNAL,
            status=PaymentStatus.PROCESSING,
            payment_metadata={"to_account_id": to_account_id}
        )

        # Execute transfer
        from_account.balance -= amount
        to_account.balance += amount

        # Create transaction records
        debit_tx = Transaction(
            account_id=from_account_id,
            external_transaction_id=f"pay-{payment.id}-debit",
            amount=-amount,
            currency=from_account.currency.value if hasattr(from_account.currency, "value") else from_account.currency,
            transaction_type=TransactionType.TRANSFER,
            description=description or f"Transfer to {to_account.account_name}",
            transaction_date=datetime.utcnow(),
            is_pending=False
        )

        credit_tx = Transaction(
            account_id=to_account_id,
            external_transaction_id=f"pay-{payment.id}-credit",
            amount=amount,
            currency=to_account.currency.value if hasattr(to_account.currency, "value") else to_account.currency,
            transaction_type=TransactionType.TRANSFER,
            description=description or f"Transfer from {from_account.account_name}",
            transaction_date=datetime.utcnow(),
            is_pending=False
        )

        # Mark payment as completed
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.utcnow()

        db.add(payment)
        db.add(debit_tx)
        db.add(credit_tx)
        db.commit()
        db.refresh(payment)

        return payment

    @staticmethod
    def initiate_interbank_transfer(
        db: Session,
        *,
        user_id: int,
        from_account_id: int,
        partner_bank_code: str,
        counterparty_account: str,
        counterparty_name: Optional[str],
        amount: Decimal,
        currency: Currency,
        purpose: Optional[str],
        consent_id: str
    ) -> InterbankTransfer:
        """Initiate interbank transfer (REQUIRES consent)."""
        # 1. Validate account
        account = (
            db.query(Account)
            .join(Account.bank_connection)
            .filter(
                Account.id == from_account_id,
                Account.bank_connection.has(user_id=user_id)
            )
            .with_for_update()
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        PaymentService._validate_currency(account, currency)
        PaymentService._validate_balance(account, amount)

        # 2. Validate consent (CRITICAL for interbank)
        partner_bank = db.query(PartnerBank).filter(PartnerBank.code == partner_bank_code).first()
        if not partner_bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Partner bank '{partner_bank_code}' not found"
            )

        consent = (
            db.query(Consent)
            .filter(
                Consent.id == consent_id,
                Consent.user_id == user_id,
                Consent.partner_bank_id == partner_bank.id,
                Consent.status == ConsentStatus.ACTIVE,
                Consent.valid_until > datetime.utcnow()
            )
            .first()
        )

        if not consent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Valid consent required for interbank transfers"
            )

        # Check if consent has PAYMENTS_WRITE scope
        if ConsentScope.PAYMENTS_WRITE.value not in (consent.scopes or []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Consent does not grant payment permissions"
            )

        # 3. Create interbank transfer
        transfer = InterbankTransfer(
            user_id=user_id,
            from_account_id=account.id,
            partner_bank_id=partner_bank.id,
            counterparty_account=counterparty_account,
            counterparty_name=counterparty_name,
            amount=amount,
            currency=currency,
            purpose=purpose,
            consent_id=consent_id,
            status=InterbankTransferStatus.INITIATED
        )

        # 4. Create linked payment
        payment = Payment(
            user_id=user_id,
            account_id=account.id,
            amount=amount,
            currency=currency,
            counterparty=counterparty_name or partner_bank.name,
            description=purpose,
            payment_type=PaymentType.INTERBANK,
            status=PaymentStatus.PROCESSING,
            consent_id=consent_id,
            payment_metadata={
                "partner_bank": partner_bank_code,
                "counterparty_account": counterparty_account
            }
        )

        # 5. Deduct from account
        account.balance -= amount

        db.add(transfer)
        db.add(payment)
        db.commit()
        db.refresh(transfer)

        return transfer

    @staticmethod
    def update_interbank_status(
        db: Session,
        *,
        transfer_id: str,
        new_status: InterbankTransferStatus,
        settled_at: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ) -> InterbankTransfer:
        """Update interbank transfer status (for webhooks/admin)."""
        transfer = db.query(InterbankTransfer).filter(InterbankTransfer.id == transfer_id).first()

        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )

        transfer.status = new_status
        if settled_at:
            transfer.settled_at = settled_at
        if metadata:
            transfer.transfer_metadata = {**(transfer.transfer_metadata or {}), **metadata}

        # Update linked payment status
        if transfer.payment:
            if new_status == InterbankTransferStatus.SETTLED:
                transfer.payment.status = PaymentStatus.COMPLETED
                transfer.payment.completed_at = datetime.utcnow()
            elif new_status == InterbankTransferStatus.FAILED:
                transfer.payment.status = PaymentStatus.FAILED

        db.commit()
        db.refresh(transfer)

        return transfer

    @staticmethod
    def list_user_payments(
        db: Session,
        *,
        user_id: int,
        payment_type: Optional[PaymentType] = None,
        status: Optional[PaymentStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Payment], int]:
        """List user's payments with filters."""
        query = db.query(Payment).filter(Payment.user_id == user_id)

        if payment_type:
            query = query.filter(Payment.payment_type == payment_type)
        if status:
            query = query.filter(Payment.status == status)

        total = query.count()
        payments = query.order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()

        return payments, total

    @staticmethod
    def list_interbank_transfers(
        db: Session,
        *,
        user_id: int,
        status: Optional[InterbankTransferStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[InterbankTransfer], int]:
        """List user's interbank transfers."""
        query = db.query(InterbankTransfer).filter(InterbankTransfer.user_id == user_id)

        if status:
            query = query.filter(InterbankTransfer.status == status)

        total = query.count()
        transfers = query.order_by(InterbankTransfer.initiated_at.desc()).offset(offset).limit(limit).all()

        return transfers, total


__all__ = ["PaymentService"]

