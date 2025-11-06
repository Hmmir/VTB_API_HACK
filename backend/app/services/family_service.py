"""Service layer for Family Banking Hub."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.account import Account, AccountVisibilityScope
from app.models.family import (
    FamilyActivityLog,
    FamilyBudget,
    FamilyBudgetPeriod,
    FamilyBudgetStatus,
    FamilyGoal,
    FamilyGoalContribution,
    FamilyGoalStatus,
    FamilyGroup,
    FamilyMember,
    FamilyMemberLimit,
    FamilyMemberLimitPeriod,
    FamilyMemberLimitStatus,
    FamilyMemberSettings,
    FamilyMemberStatus,
    FamilyNotification,
    FamilyNotificationStatus,
    FamilyNotificationType,
    FamilyRole,
    FamilyTransfer,
    FamilyTransferStatus,
    FamilyAccountVisibility,
)
from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.notification import (
    Notification as GlobalNotification,
    NotificationType as GlobalNotificationType,
    NotificationPriority,
)
from app.schemas.family import (
    FamilyBudgetCreate,
    FamilyGoalContributionCreate,
    FamilyGoalCreate,
    FamilyMemberLimitCreate,
    FamilyTransferCreate,
)


class FamilyService:
    """Business logic for Family Banking Hub."""

    INVITE_CODE_LENGTH = 10

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _require_member(db: Session, family_id: int, user_id: int, *, active: bool = True) -> FamilyMember:
        member = (
            db.query(FamilyMember)
            .filter(FamilyMember.family_id == family_id, FamilyMember.user_id == user_id)
            .first()
        )
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family member not found")
        if active and member.status != FamilyMemberStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member is not active")
        return member

    @staticmethod
    def _require_admin(member: FamilyMember) -> None:
        if member.role != FamilyRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    @staticmethod
    def _generate_invite_code(db: Session) -> str:
        for _ in range(10):
            code = secrets.token_urlsafe(FamilyService.INVITE_CODE_LENGTH)[: FamilyService.INVITE_CODE_LENGTH]
            exists = db.query(FamilyGroup).filter(FamilyGroup.invite_code == code).first()
            if not exists:
                return code
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to generate invite code")

    @staticmethod
    def _log_activity(db: Session, *, family_id: int, actor_id: Optional[int], action: str, target_type: Optional[str] = None, target_id: Optional[str] = None, metadata: Optional[dict] = None) -> None:
        log = FamilyActivityLog(
            family_id=family_id,
            actor_member_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
        )
        db.add(log)

    @staticmethod
    def _create_notification(
        db: Session,
        *,
        family_id: int,
        member_id: Optional[int],
        notification_type: FamilyNotificationType,
        payload: Optional[dict] = None,
    ) -> None:
        notification = FamilyNotification(
            family_id=family_id,
            member_id=member_id,
            notification_type=notification_type,
            payload=payload or {},
            status=FamilyNotificationStatus.NEW,
        )
        db.add(notification)

        recipients: List[int] = []
        if member_id:
            member = db.query(FamilyMember).filter(FamilyMember.id == member_id, FamilyMember.family_id == family_id).first()
            if member:
                recipients.append(member.user_id)
        else:
            admin_members = (
                db.query(FamilyMember)
                .filter(
                    FamilyMember.family_id == family_id,
                    FamilyMember.status == FamilyMemberStatus.ACTIVE,
                    FamilyMember.role == FamilyRole.ADMIN,
                )
                .all()
            )
            recipients = [m.user_id for m in admin_members]

        title, message, global_type, priority = FamilyService._build_global_notification_content(notification_type, payload)

        for user_id in recipients:
            global_notification = GlobalNotification(
                user_id=user_id,
                type=global_type,
                priority=priority,
                title=title,
                message=message,
                related_entity_type="family",
                related_entity_id=str(notification.id),
                notification_metadata=payload or {},
            )
            db.add(global_notification)

    # ------------------------------------------------------------------
    # Family management
    # ------------------------------------------------------------------
    @staticmethod
    def _build_global_notification_content(
        notification_type: FamilyNotificationType,
        payload: Optional[dict],
    ) -> Tuple[str, str, GlobalNotificationType, NotificationPriority]:
        payload = payload or {}

        if notification_type == FamilyNotificationType.LIMIT_EXCEEDED:
            title = "Превышен лимит расходов"
            message = "Семейный лимит расходов достигнут. Проверьте траты и одобрите исключения."
            return title, message, GlobalNotificationType.BUDGET_EXCEEDED, NotificationPriority.HIGH
        if notification_type == FamilyNotificationType.LIMIT_APPROACH:
            title = "Лимит расходов почти исчерпан"
            message = "Участник приближается к установленному лимиту. Рекомендуем проверить траты."
            return title, message, GlobalNotificationType.SYSTEM, NotificationPriority.MEDIUM
        if notification_type == FamilyNotificationType.BUDGET_APPROACH:
            title = "Семейный бюджет на исходе"
            message = "Совместный бюджет близок к пределу. Пересмотрите расходы в этой категории."
            return title, message, GlobalNotificationType.SYSTEM, NotificationPriority.MEDIUM
        if notification_type == FamilyNotificationType.TRANSFER_REQUEST:
            title = "Новый запрос на перевод"
            message = "Один из участников запросил перевод. Подтвердите или отклоните запрос."
            return title, message, GlobalNotificationType.SYSTEM, NotificationPriority.MEDIUM
        if notification_type == FamilyNotificationType.TRANSFER_APPROVED:
            status_value = payload.get("status") if isinstance(payload, dict) else None
            if status_value == "rejected":
                title = "Запрос на перевод отклонён"
                message = "Запрошенный перевод был отклонён администратором семьи."
                return title, message, GlobalNotificationType.TRANSFER_FAILED, NotificationPriority.MEDIUM
            title = "Перевод выполнен"
            message = "Запрошенный перевод был успешно одобрен и выполнен."
            return title, message, GlobalNotificationType.TRANSFER_COMPLETED, NotificationPriority.MEDIUM
        if notification_type == FamilyNotificationType.GOAL_COMPLETED:
            title = "Семейная цель достигнута"
            message = "Поздравляем! Общая цель достигнута. Планируйте новую цель и празднуйте результат."
            return title, message, GlobalNotificationType.GOAL_ACHIEVED, NotificationPriority.MEDIUM
        if notification_type == FamilyNotificationType.GOAL_PROGRESS:
            title = "Прогресс по семейной цели"
            message = "Цель пополнена. Продолжайте в том же духе, чтобы быстрее достичь результата."
            return title, message, GlobalNotificationType.SYSTEM, NotificationPriority.LOW

        title = "Обновление семейного хаба"
        message = "Событие Family Banking Hub требует вашего внимания."
        return title, message, GlobalNotificationType.SYSTEM, NotificationPriority.LOW

    @staticmethod
    def create_family(db: Session, *, user_id: int, name: str, description: Optional[str]) -> FamilyGroup:
        invite_code = FamilyService._generate_invite_code(db)
        family = FamilyGroup(
            name=name,
            description=description,
            created_by_user_id=user_id,
            invite_code=invite_code,
        )
        db.add(family)
        db.flush()

        member = FamilyMember(
            family_id=family.id,
            user_id=user_id,
            role=FamilyRole.ADMIN,
            status=FamilyMemberStatus.ACTIVE,
            joined_at=datetime.utcnow(),
        )
        db.add(member)
        db.flush()

        settings = FamilyMemberSettings(member_id=member.id, show_accounts=True, default_visibility="family")
        db.add(settings)
        FamilyService._log_activity(db, family_id=family.id, actor_id=member.id, action="family_created")
        db.commit()
        db.refresh(family)
        return family

    @staticmethod
    def list_families(db: Session, *, user_id: int) -> List[FamilyGroup]:
        families = (
            db.query(FamilyGroup)
            .join(FamilyMember, FamilyMember.family_id == FamilyGroup.id)
            .filter(FamilyMember.user_id == user_id)
            .all()
        )
        return families

    @staticmethod
    def get_family(db: Session, *, user_id: int, family_id: int) -> FamilyGroup:
        FamilyService._require_member(db, family_id, user_id)
        family = db.query(FamilyGroup).filter(FamilyGroup.id == family_id).first()
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
        return family

    @staticmethod
    def generate_invite(db: Session, *, family_id: int, user_id: int) -> FamilyGroup:
        member = FamilyService._require_member(db, family_id, user_id)
        FamilyService._require_admin(member)
        family = db.query(FamilyGroup).filter(FamilyGroup.id == family_id).first()
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
        family.invite_code = FamilyService._generate_invite_code(db)
        family.updated_at = datetime.utcnow()
        FamilyService._log_activity(db, family_id=family_id, actor_id=member.id, action="invite_rotated")
        db.commit()
        db.refresh(family)
        return family

    @staticmethod
    def join_family(db: Session, *, user_id: int, invite_code: str) -> FamilyGroup:
        family = db.query(FamilyGroup).filter(FamilyGroup.invite_code == invite_code).first()
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite code")

        existing = (
            db.query(FamilyMember)
            .filter(FamilyMember.family_id == family.id, FamilyMember.user_id == user_id)
            .first()
        )
        if existing:
            if existing.status == FamilyMemberStatus.ACTIVE:
                return family
            existing.status = FamilyMemberStatus.ACTIVE
            existing.joined_at = datetime.utcnow()
            db.commit()
            return family

        member = FamilyMember(
            family_id=family.id,
            user_id=user_id,
            role=FamilyRole.MEMBER,
            status=FamilyMemberStatus.ACTIVE,
            joined_at=datetime.utcnow(),
        )
        db.add(member)
        db.flush()
        settings = FamilyMemberSettings(member_id=member.id, show_accounts=True, default_visibility="family")
        db.add(settings)
        FamilyService._log_activity(db, family_id=family.id, actor_id=member.id, action="member_joined")
        db.commit()
        return family

    @staticmethod
    def update_member(
        db: Session,
        *,
        family_id: int,
        user_id: int,
        member_id: int,
        role: Optional[FamilyRole],
        status: Optional[FamilyMemberStatus],
    ) -> FamilyMember:
        actor = FamilyService._require_member(db, family_id, user_id)
        FamilyService._require_admin(actor)

        member = db.query(FamilyMember).filter(FamilyMember.id == member_id, FamilyMember.family_id == family_id).first()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        if role:
            member.role = role
        if status:
            member.status = status
            if status == FamilyMemberStatus.ACTIVE and not member.joined_at:
                member.joined_at = datetime.utcnow()
        db.commit()
        db.refresh(member)
        FamilyService._log_activity(
            db,
            family_id=family_id,
            actor_id=actor.id,
            action="member_updated",
            target_type="member",
            target_id=str(member.id),
            metadata={"role": member.role.value, "status": member.status.value},
        )
        return member

    @staticmethod
    def remove_member(db: Session, *, family_id: int, user_id: int, member_id: int) -> None:
        actor = FamilyService._require_member(db, family_id, user_id)
        FamilyService._require_admin(actor)

        member = db.query(FamilyMember).filter(FamilyMember.id == member_id, FamilyMember.family_id == family_id).first()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        if member.user_id == user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove yourself")

        db.delete(member)
        FamilyService._log_activity(
            db,
            family_id=family_id,
            actor_id=actor.id,
            action="member_removed",
            target_type="member",
            target_id=str(member_id),
        )
        db.commit()

    # ------------------------------------------------------------------
    # Budgets & Limits
    # ------------------------------------------------------------------
    @staticmethod
    def create_budget(
        db: Session,
        *,
        family_id: int,
        user_id: int,
        payload: FamilyBudgetCreate,
    ) -> FamilyBudget:
        member = FamilyService._require_member(db, family_id, user_id)
        FamilyService._require_admin(member)

        if payload.category_id:
            category = db.query(Category).filter(Category.id == payload.category_id).first()
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        budget = FamilyBudget(
            family_id=family_id,
            category_id=payload.category_id,
            name=payload.name,
            amount=payload.amount,
            period=payload.period,
            status=FamilyBudgetStatus.ACTIVE,
            start_date=payload.start_date,
            end_date=payload.end_date,
            created_by_member_id=member.id,
        )
        db.add(budget)
        FamilyService._log_activity(db, family_id=family_id, actor_id=member.id, action="budget_created", target_type="budget")
        db.commit()
        db.refresh(budget)
        return budget

    @staticmethod
    def list_budgets(db: Session, *, family_id: int, user_id: int) -> List[FamilyBudget]:
        FamilyService._require_member(db, family_id, user_id)
        return (
            db.query(FamilyBudget)
            .filter(FamilyBudget.family_id == family_id, FamilyBudget.status == FamilyBudgetStatus.ACTIVE)
            .order_by(FamilyBudget.created_at.desc())
            .all()
        )

    @staticmethod
    def create_member_limit(
        db: Session,
        *,
        family_id: int,
        user_id: int,
        payload: FamilyMemberLimitCreate,
    ) -> FamilyMemberLimit:
        actor = FamilyService._require_member(db, family_id, user_id)
        FamilyService._require_admin(actor)

        member = db.query(FamilyMember).filter(FamilyMember.id == payload.member_id, FamilyMember.family_id == family_id).first()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        if payload.category_id:
            category = db.query(Category).filter(Category.id == payload.category_id).first()
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        limit_obj = FamilyMemberLimit(
            family_id=family_id,
            member_id=payload.member_id,
            category_id=payload.category_id,
            amount=payload.amount,
            period=payload.period,
            auto_unlock=payload.auto_unlock,
            status=FamilyMemberLimitStatus.ACTIVE,
        )
        db.add(limit_obj)
        FamilyService._log_activity(
            db,
            family_id=family_id,
            actor_id=actor.id,
            action="limit_created",
            target_type="limit",
            target_id=str(limit_obj.id),
        )
        db.commit()
        db.refresh(limit_obj)
        return limit_obj

    @staticmethod
    def list_member_limits(db: Session, *, family_id: int, user_id: int) -> List[FamilyMemberLimit]:
        FamilyService._require_member(db, family_id, user_id)
        return (
            db.query(FamilyMemberLimit)
            .filter(FamilyMemberLimit.family_id == family_id, FamilyMemberLimit.status == FamilyMemberLimitStatus.ACTIVE)
            .order_by(FamilyMemberLimit.created_at.desc())
            .all()
        )

    # ------------------------------------------------------------------
    # Goals
    # ------------------------------------------------------------------
    @staticmethod
    def create_goal(db: Session, *, family_id: int, user_id: int, payload: FamilyGoalCreate) -> FamilyGoal:
        member = FamilyService._require_member(db, family_id, user_id)
        goal = FamilyGoal(
            family_id=family_id,
            name=payload.name,
            description=payload.description,
            target_amount=payload.target_amount,
            current_amount=0,
            deadline=payload.deadline,
            status=FamilyGoalStatus.ACTIVE,
            created_by_member_id=member.id,
        )
        db.add(goal)
        FamilyService._log_activity(db, family_id=family_id, actor_id=member.id, action="goal_created", target_type="goal")
        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def list_goals(db: Session, *, family_id: int, user_id: int) -> List[FamilyGoal]:
        FamilyService._require_member(db, family_id, user_id)
        return (
            db.query(FamilyGoal)
            .filter(FamilyGoal.family_id == family_id, FamilyGoal.status != FamilyGoalStatus.ARCHIVED)
            .order_by(FamilyGoal.created_at.desc())
            .all()
        )

    @staticmethod
    def contribute_goal(
        db: Session,
        *,
        family_id: int,
        user_id: int,
        goal_id: int,
        payload: FamilyGoalContributionCreate,
    ) -> FamilyGoalContribution:
        member = FamilyService._require_member(db, family_id, user_id)
        goal = db.query(FamilyGoal).filter(FamilyGoal.id == goal_id, FamilyGoal.family_id == family_id).first()
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        if goal.status != FamilyGoalStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Goal is not active")

        contribution = FamilyGoalContribution(
            goal_id=goal_id,
            member_id=member.id,
            amount=payload.amount,
            source_account_id=payload.source_account_id,
            scheduled=payload.scheduled,
            schedule_rule=payload.schedule_rule,
        )
        goal.current_amount += Decimal(str(payload.amount))
        if goal.current_amount >= goal.target_amount:
            goal.status = FamilyGoalStatus.COMPLETED
            FamilyService._create_notification(
                db,
                family_id=family_id,
                member_id=None,
                notification_type=FamilyNotificationType.GOAL_COMPLETED,
                payload={"goal_id": goal.id, "name": goal.name},
            )
        else:
            FamilyService._create_notification(
                db,
                family_id=family_id,
                member_id=None,
                notification_type=FamilyNotificationType.GOAL_PROGRESS,
                payload={"goal_id": goal.id, "name": goal.name, "current_amount": str(goal.current_amount)},
            )

        db.add(contribution)
        FamilyService._log_activity(
            db,
            family_id=family_id,
            actor_id=member.id,
            action="goal_contribution",
            target_type="goal",
            target_id=str(goal_id),
            metadata={"amount": str(payload.amount)},
        )
        db.commit()
        db.refresh(contribution)
        return contribution

    # ------------------------------------------------------------------
    # Transfers
    # ------------------------------------------------------------------
    @staticmethod
    def create_transfer(
        db: Session,
        *,
        family_id: int,
        user_id: int,
        payload: FamilyTransferCreate,
    ) -> FamilyTransfer:
        requester = FamilyService._require_member(db, family_id, user_id)
        to_member = db.query(FamilyMember).filter(FamilyMember.id == payload.to_member_id, FamilyMember.family_id == family_id).first()
        if not to_member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

        amount_decimal = Decimal(str(payload.amount))
        exceeds = FamilyService._check_member_limits(
            db,
            family_id=family_id,
            member=requester,
            amount=amount_decimal,
        )
        if exceeds and requester.role != FamilyRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Перевод превышает установленный лимит",
            )

        transfer = FamilyTransfer(
            family_id=family_id,
            from_member_id=requester.id,
            to_member_id=payload.to_member_id,
            from_account_id=payload.from_account_id,
            to_account_id=payload.to_account_id,
            requested_by_member_id=requester.id,
            amount=amount_decimal,
            currency=payload.currency,
            description=payload.description,
            status=FamilyTransferStatus.PENDING if requester.role != FamilyRole.ADMIN else FamilyTransferStatus.APPROVED,
        )

        db.add(transfer)
        db.flush()

        if requester.role != FamilyRole.ADMIN:
            FamilyService._create_notification(
                db,
                family_id=family_id,
                member_id=None,
                notification_type=FamilyNotificationType.TRANSFER_REQUEST,
                payload={
                    "transfer_id": transfer.id,
                    "from_member_id": requester.id,
                    "to_member_id": to_member.id,
                    "amount": payload.amount,
                },
            )
        else:
            transfer.approved_by_member_id = requester.id
            transfer.approved_at = datetime.utcnow()
            transfer.status = FamilyTransferStatus.APPROVED

        FamilyService._log_activity(
            db,
            family_id=family_id,
            actor_id=requester.id,
            action="transfer_created",
            target_type="transfer",
            target_id=str(transfer.id),
            metadata={"amount": payload.amount},
        )
        db.commit()
        db.refresh(transfer)
        return transfer

    @staticmethod
    def approve_transfer(
        db: Session,
        *,
        family_id: int,
        user_id: int,
        transfer_id: int,
        approve: bool,
        reason: Optional[str],
    ) -> FamilyTransfer:
        actor = FamilyService._require_member(db, family_id, user_id)
        FamilyService._require_admin(actor)

        transfer = db.query(FamilyTransfer).filter(FamilyTransfer.id == transfer_id, FamilyTransfer.family_id == family_id).first()
        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
        if transfer.status not in (FamilyTransferStatus.PENDING, FamilyTransferStatus.APPROVED):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer already processed")

        if not approve:
            transfer.status = FamilyTransferStatus.REJECTED
            transfer.failed_reason = reason
            FamilyService._create_notification(
                db,
                family_id=family_id,
                member_id=transfer.from_member_id,
                notification_type=FamilyNotificationType.TRANSFER_APPROVED,
                payload={"transfer_id": transfer.id, "status": "rejected", "reason": reason},
            )
            db.commit()
            return transfer

        transfer.approved_by_member_id = actor.id
        transfer.approved_at = datetime.utcnow()

        # Execute internal transfer between users
        if transfer.from_account_id and transfer.to_account_id:
            FamilyService._execute_transfer(
                db,
                family_id=family_id,
                transfer=transfer,
                amount=Decimal(str(transfer.amount)),
            )
            transfer.executed_at = datetime.utcnow()
            transfer.status = FamilyTransferStatus.EXECUTED
        else:
            transfer.status = FamilyTransferStatus.APPROVED

        if transfer.from_member_id:
            FamilyService._evaluate_member_limits(db, family_id=family_id, member_id=transfer.from_member_id)
        FamilyService._evaluate_family_budgets(db, family_id=family_id)

        FamilyService._create_notification(
            db,
            family_id=family_id,
            member_id=transfer.from_member_id,
            notification_type=FamilyNotificationType.TRANSFER_APPROVED,
            payload={"transfer_id": transfer.id, "status": "approved"},
        )
        db.commit()
        db.refresh(transfer)
        return transfer

    @staticmethod
    def list_transfers(db: Session, *, family_id: int, user_id: int) -> List[FamilyTransfer]:
        FamilyService._require_member(db, family_id, user_id)
        return (
            db.query(FamilyTransfer)
            .filter(FamilyTransfer.family_id == family_id)
            .order_by(FamilyTransfer.created_at.desc())
            .all()
        )

    # ------------------------------------------------------------------
    # Notifications & analytics
    # ------------------------------------------------------------------
    @staticmethod
    def list_notifications(db: Session, *, family_id: int, user_id: int) -> List[FamilyNotification]:
        FamilyService._require_member(db, family_id, user_id)
        notifications = (
            db.query(FamilyNotification)
            .filter(FamilyNotification.family_id == family_id)
            .order_by(FamilyNotification.created_at.desc())
            .all()
        )
        return notifications

    @staticmethod
    def mark_notification_read(db: Session, *, family_id: int, user_id: int, notification_id: int) -> FamilyNotification:
        member = FamilyService._require_member(db, family_id, user_id)
        notification = (
            db.query(FamilyNotification)
            .filter(
                FamilyNotification.id == notification_id,
                FamilyNotification.family_id == family_id,
            )
            .first()
        )
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        if notification.status != FamilyNotificationStatus.READ:
            notification.status = FamilyNotificationStatus.READ
            notification.read_at = datetime.utcnow()
            db.commit()
        return notification

    @staticmethod
    def get_analytics_summary(db: Session, *, family_id: int, user_id: int) -> dict:
        FamilyService._require_member(db, family_id, user_id)

        members = (
            db.query(FamilyMember)
            .filter(FamilyMember.family_id == family_id, FamilyMember.status == FamilyMemberStatus.ACTIVE)
            .all()
        )

        accounts = db.query(Account).filter(Account.primary_family_id == family_id).all()
        account_ids = [a.id for a in accounts]
        total_balance = float(sum((a.balance or 0) for a in accounts)) if accounts else 0.0

        transactions = []
        total_income = 0.0
        total_expense = 0.0
        category_spending = []

        if account_ids:
            transactions = db.query(Transaction).filter(Transaction.account_id.in_(account_ids)).all()
            for tx in transactions:
                amount = float(tx.amount)
                if tx.transaction_type == TransactionType.INCOME:
                    total_income += amount
                elif tx.transaction_type == TransactionType.EXPENSE:
                    total_expense += abs(amount)

            category_rows = (
                db.query(Transaction.category_id, func.sum(Transaction.amount))
                .filter(Transaction.account_id.in_(account_ids), Transaction.category_id.isnot(None))
                .group_by(Transaction.category_id)
                .all()
            )
            for category_id, total in category_rows:
                category_spending.append({
                    "category_id": category_id,
                    "amount": float(abs(total or 0)),
                })

        member_spending = []
        for member in members:
            member_accounts = [
                a for a in accounts if a.bank_connection and a.bank_connection.user_id == member.user_id
            ]
            member_balance = float(sum((a.balance or 0) for a in member_accounts)) if member_accounts else 0.0
            member_spending.append(
                {
                    "member_id": member.id,
                    "user_id": member.user_id,
                    "total_balance": member_balance,
                }
            )

        goals = (
            db.query(FamilyGoal)
            .filter(FamilyGoal.family_id == family_id, FamilyGoal.status != FamilyGoalStatus.ARCHIVED)
            .all()
        )

        budgets = (
            db.query(FamilyBudget)
            .filter(FamilyBudget.family_id == family_id, FamilyBudget.status == FamilyBudgetStatus.ACTIVE)
            .all()
        )

        summary = {
            "total_balance": total_balance,
            "total_income": total_income,
            "total_expense": total_expense,
            "member_spending": member_spending,
            "category_spending": category_spending,
            "goals": [
                {
                    "id": goal.id,
                    "name": goal.name,
                    "target_amount": float(goal.target_amount),
                    "current_amount": float(goal.current_amount),
                    "status": goal.status.value,
                }
                for goal in goals
            ],
            "budgets": [
                {
                    "id": budget.id,
                    "name": budget.name,
                    "amount": float(budget.amount),
                    "period": budget.period.value,
                }
                for budget in budgets
            ],
        }

        return summary

    # ------------------------------------------------------------------
    # Account visibility
    # ------------------------------------------------------------------
    @staticmethod
    def update_account_visibility(
        db: Session,
        *,
        family_id: int,
        user_id: int,
        account_id: int,
        visibility_scope: AccountVisibilityScope,
    ) -> FamilyAccountVisibility:
        member = FamilyService._require_member(db, family_id, user_id)
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        fav = (
            db.query(FamilyAccountVisibility)
            .filter(
                FamilyAccountVisibility.family_id == family_id,
                FamilyAccountVisibility.account_id == account_id,
            )
            .first()
        )
        if not fav:
            fav = FamilyAccountVisibility(
                family_id=family_id,
                account_id=account_id,
                visibility_scope=visibility_scope.value,
            )
            db.add(fav)
        else:
            fav.visibility_scope = visibility_scope.value
            fav.updated_at = datetime.utcnow()

        # Update account primary family if needed
        if visibility_scope == AccountVisibilityScope.FAMILY:
            account.primary_family_id = family_id
        else:
            if account.primary_family_id == family_id:
                account.primary_family_id = None

        account.visibility_scope = visibility_scope
        FamilyService._log_activity(
            db,
            family_id=family_id,
            actor_id=member.id,
            action="account_visibility_changed",
            target_type="account",
            target_id=str(account_id),
            metadata={"visibility": visibility_scope.value},
        )
        db.commit()
        db.refresh(fav)
        return fav

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _execute_transfer(
        db: Session,
        *,
        family_id: int,
        transfer: FamilyTransfer,
        amount: Decimal,
    ) -> None:
        """Execute balance changes for a family transfer."""
        from_account = (
            db.query(Account)
            .join(Account.bank_connection)
            .filter(
                Account.id == transfer.from_account_id,
                Account.bank_connection.has(user_id=transfer.from_member.user_id),
            )
            .with_for_update()
            .first()
        )
        to_account = (
            db.query(Account)
            .join(Account.bank_connection)
            .filter(
                Account.id == transfer.to_account_id,
                Account.bank_connection.has(user_id=transfer.to_member.user_id),
            )
            .with_for_update()
            .first()
        )

        if not from_account or not to_account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found for transfer")

        if from_account.currency != to_account.currency:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cross-currency transfers not supported")

        if from_account.balance < amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds for transfer")

        from_account.balance -= amount
        to_account.balance += amount

        debit_tx = Transaction(
            account_id=from_account.id,
            external_transaction_id=f"family-{transfer.id}-debit",
            amount=-amount,
            currency=from_account.currency.value if hasattr(from_account.currency, "value") else from_account.currency,
            transaction_type=TransactionType.TRANSFER,
            description=transfer.description or f"Transfer to {to_account.account_name}",
            transaction_date=datetime.utcnow(),
            is_pending=False,
        )

        credit_tx = Transaction(
            account_id=to_account.id,
            external_transaction_id=f"family-{transfer.id}-credit",
            amount=amount,
            currency=to_account.currency.value if hasattr(to_account.currency, "value") else to_account.currency,
            transaction_type=TransactionType.TRANSFER,
            description=transfer.description or f"Transfer from {from_account.account_name}",
            transaction_date=datetime.utcnow(),
            is_pending=False,
        )

        db.add(debit_tx)
        db.add(credit_tx)

    @staticmethod
    def _get_period_start(period: FamilyMemberLimitPeriod | FamilyBudgetPeriod) -> datetime:
        now = datetime.utcnow()
        if period == FamilyMemberLimitPeriod.WEEKLY or period == FamilyBudgetPeriod.WEEKLY:
            return now - timedelta(days=7)
        return now - timedelta(days=30)

    @staticmethod
    def _calculate_member_spending(
        db: Session,
        *,
        member: FamilyMember,
        start: datetime,
        category_id: Optional[int] = None,
    ) -> Decimal:
        query = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .join(Transaction.account)
            .join(Account.bank_connection)
            .filter(
                Account.bank_connection.has(user_id=member.user_id),
                Transaction.transaction_date >= start,
                Transaction.amount < 0,
            )
        )
        if category_id:
            query = query.filter(Transaction.category_id == category_id)

        spent = query.scalar() or 0
        return Decimal(str(abs(spent)))

    @staticmethod
    def _check_member_limits(
        db: Session,
        *,
        family_id: int,
        member: FamilyMember,
        amount: Decimal,
    ) -> bool:
        limits = (
            db.query(FamilyMemberLimit)
            .filter(
                FamilyMemberLimit.family_id == family_id,
                FamilyMemberLimit.member_id == member.id,
                FamilyMemberLimit.status == FamilyMemberLimitStatus.ACTIVE,
            )
            .all()
        )
        exceeded = False
        for limit_obj in limits:
            period_start = FamilyService._get_period_start(limit_obj.period)
            spent = FamilyService._calculate_member_spending(
                db,
                member=member,
                start=period_start,
                category_id=limit_obj.category_id,
            )
            threshold = Decimal(str(limit_obj.amount))
            projected = spent + amount

            if projected >= threshold:
                exceeded = True
                FamilyService._create_notification(
                    db,
                    family_id=family_id,
                    member_id=member.id,
                    notification_type=FamilyNotificationType.LIMIT_EXCEEDED,
                    payload={
                        "member_id": member.id,
                        "limit_id": limit_obj.id,
                        "limit_amount": str(threshold),
                        "period": limit_obj.period.value,
                        "spent": str(projected),
                    },
                )
            elif projected >= threshold * Decimal("0.8"):
                FamilyService._create_notification(
                    db,
                    family_id=family_id,
                    member_id=member.id,
                    notification_type=FamilyNotificationType.LIMIT_APPROACH,
                    payload={
                        "member_id": member.id,
                        "limit_id": limit_obj.id,
                        "limit_amount": str(threshold),
                        "period": limit_obj.period.value,
                        "spent": str(projected),
                    },
                )
        return exceeded

    @staticmethod
    def _evaluate_member_limits(db: Session, *, family_id: int, member_id: int) -> None:
        member = db.query(FamilyMember).filter(FamilyMember.id == member_id, FamilyMember.family_id == family_id).first()
        if not member:
            return
        limits = (
            db.query(FamilyMemberLimit)
            .filter(
                FamilyMemberLimit.family_id == family_id,
                FamilyMemberLimit.member_id == member_id,
                FamilyMemberLimit.status == FamilyMemberLimitStatus.ACTIVE,
            )
            .all()
        )
        for limit_obj in limits:
            period_start = FamilyService._get_period_start(limit_obj.period)
            spent = FamilyService._calculate_member_spending(
                db,
                member=member,
                start=period_start,
                category_id=limit_obj.category_id,
            )
            threshold = Decimal(str(limit_obj.amount))
            if spent >= threshold:
                FamilyService._create_notification(
                    db,
                    family_id=family_id,
                    member_id=member.id,
                    notification_type=FamilyNotificationType.LIMIT_EXCEEDED,
                    payload={
                        "member_id": member.id,
                        "limit_id": limit_obj.id,
                        "limit_amount": str(threshold),
                        "period": limit_obj.period.value,
                        "spent": str(spent),
                    },
                )
            elif spent >= threshold * Decimal("0.8"):
                FamilyService._create_notification(
                    db,
                    family_id=family_id,
                    member_id=member.id,
                    notification_type=FamilyNotificationType.LIMIT_APPROACH,
                    payload={
                        "member_id": member.id,
                        "limit_id": limit_obj.id,
                        "limit_amount": str(threshold),
                        "period": limit_obj.period.value,
                        "spent": str(spent),
                    },
                )

    @staticmethod
    def _evaluate_family_budgets(db: Session, *, family_id: int) -> None:
        budgets = (
            db.query(FamilyBudget)
            .filter(FamilyBudget.family_id == family_id, FamilyBudget.status == FamilyBudgetStatus.ACTIVE)
            .all()
        )
        if not budgets:
            return

        accounts = db.query(Account).filter(Account.primary_family_id == family_id).all()
        account_ids = [account.id for account in accounts]
        if not account_ids:
            return

        for budget in budgets:
            period_start = FamilyService._get_period_start(budget.period)
            query = (
                db.query(func.coalesce(func.sum(Transaction.amount), 0))
                .filter(
                    Transaction.account_id.in_(account_ids),
                    Transaction.transaction_date >= period_start,
                    Transaction.amount < 0,
                )
            )
            if budget.category_id:
                query = query.filter(Transaction.category_id == budget.category_id)

            spent_value = query.scalar() or 0
            spent = Decimal(str(abs(spent_value)))
            threshold = Decimal(str(budget.amount))

            if spent >= threshold:
                FamilyService._create_notification(
                    db,
                    family_id=family_id,
                    member_id=None,
                    notification_type=FamilyNotificationType.LIMIT_EXCEEDED,
                    payload={
                        "budget_id": budget.id,
                        "budget_name": budget.name,
                        "amount": str(threshold),
                        "spent": str(spent),
                        "type": "budget",
                    },
                )
            elif spent >= threshold * Decimal("0.8"):
                FamilyService._create_notification(
                    db,
                    family_id=family_id,
                    member_id=None,
                    notification_type=FamilyNotificationType.BUDGET_APPROACH,
                    payload={
                        "budget_id": budget.id,
                        "budget_name": budget.name,
                        "amount": str(threshold),
                        "spent": str(spent),
                    },
                )


__all__ = ["FamilyService"]


