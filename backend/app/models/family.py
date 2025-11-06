"""Family banking hub models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class FamilyRole(str, Enum):
    """Family member role."""

    ADMIN = "admin"
    MEMBER = "member"


class FamilyMemberStatus(str, Enum):
    """Family member status."""

    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"


class FamilyBudgetPeriod(str, Enum):
    """Family budget period."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"


class FamilyBudgetStatus(str, Enum):
    """Family budget status."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class FamilyMemberLimitPeriod(str, Enum):
    """Family member limit period."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"


class FamilyMemberLimitStatus(str, Enum):
    """Family member limit status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class FamilyGoalStatus(str, Enum):
    """Family goal status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class FamilyTransferStatus(str, Enum):
    """Family transfer status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FamilyNotificationType(str, Enum):
    """Family notification type."""

    LIMIT_APPROACH = "limit_approach"
    LIMIT_EXCEEDED = "limit_exceeded"
    BUDGET_APPROACH = "budget_approach"
    TRANSFER_REQUEST = "transfer_request"
    TRANSFER_APPROVED = "transfer_approved"
    GOAL_PROGRESS = "goal_progress"
    GOAL_COMPLETED = "goal_completed"


class FamilyNotificationStatus(str, Enum):
    """Family notification status."""

    NEW = "new"
    READ = "read"
    ARCHIVED = "archived"


class FamilyGroup(Base):
    """Family group model."""

    __tablename__ = "family_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invite_code = Column(String(64), nullable=False, unique=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    members = relationship("FamilyMember", back_populates="family", cascade="all, delete-orphan")
    budgets = relationship("FamilyBudget", back_populates="family", cascade="all, delete-orphan")
    member_limits = relationship("FamilyMemberLimit", back_populates="family", cascade="all, delete-orphan")
    goals = relationship("FamilyGoal", back_populates="family", cascade="all, delete-orphan")
    transfers = relationship("FamilyTransfer", back_populates="family", cascade="all, delete-orphan")
    notifications = relationship("FamilyNotification", back_populates="family", cascade="all, delete-orphan")
    activities = relationship("FamilyActivityLog", back_populates="family", cascade="all, delete-orphan")


class FamilyMember(Base):
    """Family member model."""

    __tablename__ = "family_members"
    __table_args__ = (
        UniqueConstraint("family_id", "user_id", name="uq_family_member"),
    )

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(FamilyRole, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FamilyRole.MEMBER)
    status = Column(SQLEnum(FamilyMemberStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FamilyMemberStatus.PENDING)
    joined_at = Column(DateTime, nullable=True)

    family = relationship("FamilyGroup", back_populates="members")
    user = relationship("User", backref="family_memberships")
    settings = relationship("FamilyMemberSettings", back_populates="member", uselist=False, cascade="all, delete-orphan")
    limits = relationship("FamilyMemberLimit", back_populates="member", cascade="all, delete-orphan")
    transfers_sent = relationship(
        "FamilyTransfer",
        foreign_keys="FamilyTransfer.from_member_id",
        back_populates="from_member",
    )
    transfers_received = relationship(
        "FamilyTransfer",
        foreign_keys="FamilyTransfer.to_member_id",
        back_populates="to_member",
    )
    goal_contributions = relationship("FamilyGoalContribution", back_populates="member", cascade="all, delete-orphan")


class FamilyMemberSettings(Base):
    """Per-member settings inside family."""

    __tablename__ = "family_member_settings"

    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False, unique=True)
    show_accounts = Column(Boolean, default=True, nullable=False)
    default_visibility = Column(String(32), default="family", nullable=False)
    custom_limits = Column(JSON, nullable=True)

    member = relationship("FamilyMember", back_populates="settings")


class FamilyBudget(Base):
    """Family budget model."""

    __tablename__ = "family_budgets"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    period = Column(SQLEnum(FamilyBudgetPeriod, values_callable=lambda x: [e.value for e in x]), nullable=False)
    status = Column(SQLEnum(FamilyBudgetStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FamilyBudgetStatus.ACTIVE)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_by_member_id = Column(Integer, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    family = relationship("FamilyGroup", back_populates="budgets")
    created_by_member = relationship("FamilyMember", foreign_keys=[created_by_member_id])
    category = relationship("Category")


class FamilyMemberLimit(Base):
    """Family member spending limit."""

    __tablename__ = "family_member_limits"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    period = Column(SQLEnum(FamilyMemberLimitPeriod, values_callable=lambda x: [e.value for e in x]), nullable=False)
    status = Column(SQLEnum(FamilyMemberLimitStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FamilyMemberLimitStatus.ACTIVE)
    auto_unlock = Column(Boolean, default=False, nullable=False)
    reset_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    family = relationship("FamilyGroup", back_populates="member_limits")
    member = relationship("FamilyMember", back_populates="limits")
    category = relationship("Category")


class FamilyGoal(Base):
    """Family savings/spending goal."""

    __tablename__ = "family_goals"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    current_amount = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    deadline = Column(Date, nullable=True)
    status = Column(SQLEnum(FamilyGoalStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FamilyGoalStatus.ACTIVE)
    created_by_member_id = Column(Integer, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    family = relationship("FamilyGroup", back_populates="goals")
    created_by_member = relationship("FamilyMember", foreign_keys=[created_by_member_id])
    contributions = relationship("FamilyGoalContribution", back_populates="goal", cascade="all, delete-orphan")


class FamilyGoalContribution(Base):
    """Contribution towards a family goal."""

    __tablename__ = "family_goal_contributions"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("family_goals.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    source_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    scheduled = Column(Boolean, default=False, nullable=False)
    schedule_rule = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    goal = relationship("FamilyGoal", back_populates="contributions")
    member = relationship("FamilyMember", back_populates="goal_contributions")
    source_account = relationship("Account")


class FamilyTransfer(Base):
    """Transfers inside a family."""

    __tablename__ = "family_transfers"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False)
    from_member_id = Column(Integer, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True)
    to_member_id = Column(Integer, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True)
    from_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    requested_by_member_id = Column(Integer, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True)
    approved_by_member_id = Column(Integer, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, default="RUB")
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(FamilyTransferStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FamilyTransferStatus.PENDING)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    failed_reason = Column(Text, nullable=True)

    family = relationship("FamilyGroup", back_populates="transfers")
    from_member = relationship("FamilyMember", foreign_keys=[from_member_id], back_populates="transfers_sent")
    to_member = relationship("FamilyMember", foreign_keys=[to_member_id], back_populates="transfers_received")
    requested_by_member = relationship("FamilyMember", foreign_keys=[requested_by_member_id])
    approved_by_member = relationship("FamilyMember", foreign_keys=[approved_by_member_id])
    from_account = relationship("Account", foreign_keys=[from_account_id])
    to_account = relationship("Account", foreign_keys=[to_account_id])


class FamilyNotification(Base):
    """Family notification model."""

    __tablename__ = "family_notifications"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True)
    notification_type = Column(SQLEnum(FamilyNotificationType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(SQLEnum(FamilyNotificationStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FamilyNotificationStatus.NEW)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)

    family = relationship("FamilyGroup", back_populates="notifications")
    member = relationship("FamilyMember")


class FamilyActivityLog(Base):
    """Audit log for family actions."""

    __tablename__ = "family_activity_log"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False)
    actor_member_id = Column(Integer, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(128), nullable=False)
    target_type = Column(String(128), nullable=True)
    target_id = Column(String(128), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    family = relationship("FamilyGroup", back_populates="activities")
    actor_member = relationship("FamilyMember")


class FamilyAccountVisibility(Base):
    """Overrides visibility of accounts for a specific family."""

    __tablename__ = "family_account_visibility"
    __table_args__ = (
        UniqueConstraint("family_id", "account_id", name="uq_family_account_visibility"),
    )

    id = Column(Integer, primary_key=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    visibility_scope = Column(String(32), nullable=False, default="family")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    family = relationship("FamilyGroup")
    account = relationship("Account")


