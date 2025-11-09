"""Family transfers service."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.family import (
    FamilyTransfer,
    FamilyTransferStatus,
    FamilyActivityLog,
    FamilyNotification,
    FamilyNotificationType,
)
from app.models.transaction import Transaction, TransactionType
from app.schemas.family import FamilyTransferCreate, FamilyTransferApprove
from app.services.family_budget_service import FamilyBudgetService
from app.services.family_service import FamilyService


class FamilyTransferService:
    """Service for managing family transfers."""

    @staticmethod
    def _apply_transfer_effects(db: Session, transfer: FamilyTransfer) -> None:
        """Apply balance updates and create transaction records for an approved transfer."""
        amount = Decimal(transfer.amount)
        now = datetime.utcnow()

        # Списание со счета отправителя
        if transfer.from_account_id:
            source_account = db.query(Account).filter(Account.id == transfer.from_account_id).with_for_update().first()
            if source_account:
                source_account.balance -= amount
                db.add(source_account)

                debit_tx = Transaction(
                    account_id=transfer.from_account_id,
                    external_transaction_id=f"FAMILY_TRANSFER_{transfer.id}_DEBIT_{uuid.uuid4().hex}",
                    amount=-amount,
                    description=f"Семейный перевод #{transfer.id}" + (f": {transfer.description}" if transfer.description else ""),
                    transaction_date=now,
                    transaction_type=TransactionType.TRANSFER,
                    category_id=None,
                )
                db.add(debit_tx)

        # Зачисление на счет получателя
        if transfer.to_account_id:
            destination_account = db.query(Account).filter(Account.id == transfer.to_account_id).with_for_update().first()
            if destination_account:
                destination_account.balance += amount
                db.add(destination_account)

                credit_tx = Transaction(
                    account_id=transfer.to_account_id,
                    external_transaction_id=f"FAMILY_TRANSFER_{transfer.id}_CREDIT_{uuid.uuid4().hex}",
                    amount=amount,
                    description=f"Семейный перевод #{transfer.id}" + (f": {transfer.description}" if transfer.description else ""),
                    transaction_date=now,
                    transaction_type=TransactionType.TRANSFER,
                    category_id=None,
                )
                db.add(credit_tx)

    @staticmethod
    def create_transfer(
        db: Session,
        family_id: int,
        from_member_id: int,
        data: FamilyTransferCreate,
        user_id: int
    ) -> FamilyTransfer:
        """Create family transfer request."""
        if not FamilyService.is_member(db, family_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only family members can create transfers"
            )

        # Валидация - должен быть указан либо to_member_id, либо to_account_id
        if not data.to_member_id and not data.to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Укажите получателя (to_member_id) или счет назначения (to_account_id)"
            )

        # Check if limit would be exceeded
        exceeded, limit = FamilyBudgetService.check_limit_exceeded(
            db, from_member_id, None, data.amount
        )

        # Create transfer - ВСЕГДА pending, требует одобрения администратора
        transfer = FamilyTransfer(
            family_id=family_id,
            from_member_id=from_member_id,
            to_member_id=data.to_member_id,
            from_account_id=data.from_account_id,
            to_account_id=data.to_account_id,
            amount=data.amount,
            currency=data.currency,
            description=data.description,
            status=FamilyTransferStatus.PENDING  # Требует одобрения администратора
        )
        db.add(transfer)
        db.flush()

        # Create notification
        notification = FamilyNotification(
            family_id=family_id,
            member_id=None,  # Notify all admins
            type=FamilyNotificationType.TRANSFER_REQUEST if exceeded else FamilyNotificationType.TRANSFER_APPROVED,
            payload={
                "transfer_id": transfer.id,
                "from_member_id": from_member_id,
                "to_member_id": data.to_member_id,
                "to_account_id": data.to_account_id,  # Добавляем to_account_id для отображения
                "amount": str(data.amount),
                "limit_exceeded": exceeded
            },
            status="new"
        )
        db.add(notification)

        # Log activity
        log = FamilyActivityLog(
            family_id=family_id,
            actor_id=user_id,
            action="created_transfer",
            target="family_transfer",
            action_metadata={
                "transfer_id": transfer.id,
                "amount": str(data.amount),
                "limit_exceeded": exceeded
            }
        )
        db.add(log)

        # Создаем транзакции если перевод одобрен и указаны счета
        if transfer.status == FamilyTransferStatus.APPROVED:
            FamilyTransferService._apply_transfer_effects(db, transfer)

        db.commit()
        db.refresh(transfer)
        return transfer

    @staticmethod
    def approve_transfer(
        db: Session,
        transfer_id: int,
        data: FamilyTransferApprove,
        user_id: int
    ) -> FamilyTransfer:
        """Approve or reject transfer."""
        transfer = db.query(FamilyTransfer).filter(FamilyTransfer.id == transfer_id).first()
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )

        if not FamilyService.is_admin(db, transfer.family_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can approve transfers"
            )

        if transfer.status != FamilyTransferStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer is not pending"
            )

        if data.approved:
            transfer.status = FamilyTransferStatus.APPROVED
            transfer.approved_by = user_id
            notif_type = FamilyNotificationType.TRANSFER_APPROVED
            FamilyTransferService._apply_transfer_effects(db, transfer)
        else:
            transfer.status = FamilyTransferStatus.REJECTED
            notif_type = FamilyNotificationType.TRANSFER_REJECTED

        # Create notification
        notification = FamilyNotification(
            family_id=transfer.family_id,
            member_id=transfer.from_member_id,
            type=notif_type,
            payload={
                "transfer_id": transfer_id,
                "from_member_id": transfer.from_member_id,
                "to_member_id": transfer.to_member_id,
                "to_account_id": transfer.to_account_id,  # Добавляем to_account_id
                "amount": str(transfer.amount),
                "approved": data.approved,
                "reason": data.reason
            },
            status="new"
        )
        db.add(notification)

        # Log activity
        log = FamilyActivityLog(
            family_id=transfer.family_id,
            actor_id=user_id,
            action="approved_transfer" if data.approved else "rejected_transfer",
            target="family_transfer",
            action_metadata={"transfer_id": transfer_id}
        )
        db.add(log)

        db.commit()
        db.refresh(transfer)
        return transfer

    @staticmethod
    def execute_transfer(
        db: Session,
        transfer_id: int
    ) -> FamilyTransfer:
        """Execute approved transfer."""
        transfer = db.query(FamilyTransfer).filter(FamilyTransfer.id == transfer_id).first()
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )

        if transfer.status != FamilyTransferStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer is not approved"
            )

        # TODO: Integrate with actual payment service to execute transfer
        # For now, just mark as executed
        transfer.status = FamilyTransferStatus.EXECUTED
        transfer.executed_at = datetime.utcnow()

        # Create notification
        notification = FamilyNotification(
            family_id=transfer.family_id,
            member_id=None,
            type=FamilyNotificationType.TRANSFER_EXECUTED,
            payload={
                "transfer_id": transfer_id,
                "from_member_id": transfer.from_member_id,
                "to_member_id": transfer.to_member_id,
                "amount": str(transfer.amount)
            },
            status="new"
        )
        db.add(notification)

        db.commit()
        db.refresh(transfer)
        return transfer

    @staticmethod
    def get_family_transfers(
        db: Session,
        family_id: int,
        member_id: Optional[int] = None
    ) -> List[FamilyTransfer]:
        """Get family transfers."""
        query = db.query(FamilyTransfer).filter(FamilyTransfer.family_id == family_id)

        if member_id:
            query = query.filter(
                or_(
                    FamilyTransfer.from_member_id == member_id,
                    FamilyTransfer.to_member_id == member_id
                )
            )

        return query.order_by(FamilyTransfer.created_at.desc()).all()

