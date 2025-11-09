"""Family Banking Hub models."""
import enum
import secrets
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Boolean,
    Numeric,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


def generate_invite_code() -> str:
    """Generate unique invite code for family group."""
    return secrets.token_urlsafe(16)


class FamilyRole(str, enum.Enum):
    """Family member roles."""
    ADMIN = "admin"
    MEMBER = "member"


class FamilyMemberStatus(str, enum.Enum):
    """Family member status."""
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"


class FamilyBudgetPeriod(str, enum.Enum):
    """Family budget period."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class FamilyGoalStatus(str, enum.Enum):
    """Family goal status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class FamilyTransferStatus(str, enum.Enum):
    """Family transfer status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


class FamilyNotificationType(str, enum.Enum):
    """Family notification types."""
    LIMIT_APPROACH = "limit_approach"
    LIMIT_EXCEEDED = "limit_exceeded"
    BUDGET_APPROACH = "budget_approach"
    BUDGET_EXCEEDED = "budget_exceeded"
    TRANSFER_REQUEST = "transfer_request"
    TRANSFER_APPROVED = "transfer_approved"
    TRANSFER_REJECTED = "transfer_rejected"
    TRANSFER_EXECUTED = "transfer_executed"
    GOAL_PROGRESS = "goal_progress"
    GOAL_COMPLETED = "goal_completed"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"


class AccountVisibility(str, enum.Enum):
    """Account visibility scope."""
    PRIVATE = "private"
    FAMILY = "family"


class FamilyGroup(Base):
    """Family group model."""
    
    __tablename__ = "family_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invite_code = Column(String(255), unique=True, nullable=False, default=generate_invite_code, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], backref="created_families")
    members = relationship("FamilyMember", back_populates="family", cascade="all, delete-orphan")
    budgets = relationship("FamilyBudget", back_populates="family", cascade="all, delete-orphan")
    limits = relationship("FamilyMemberLimit", back_populates="family", cascade="all, delete-orphan")
    goals = relationship("FamilyGoal", back_populates="family", cascade="all, delete-orphan")
    transfers = relationship("FamilyTransfer", back_populates="family", cascade="all, delete-orphan")
    notifications = relationship("FamilyNotification", back_populates="family", cascade="all, delete-orphan")
    activity_logs = relationship("FamilyActivityLog", back_populates="family", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FamilyGroup(id={self.id}, name='{self.name}')>"


class FamilyMember(Base):
    """Family member model."""
    
    __tablename__ = "family_members"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(SQLEnum(FamilyRole, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FamilyRole.MEMBER)
    status = Column(SQLEnum(FamilyMemberStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FamilyMemberStatus.PENDING)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    family = relationship("FamilyGroup", back_populates="members")
    user = relationship("User", backref="family_memberships")
    settings = relationship("FamilyMemberSettings", back_populates="member", uselist=False, cascade="all, delete-orphan")
    limits = relationship("FamilyMemberLimit", back_populates="member", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_family_user', 'family_id', 'user_id', unique=True),
    )
    
    def __repr__(self):
        return f"<FamilyMember(id={self.id}, family_id={self.family_id}, user_id={self.user_id}, role={self.role})>"


class FamilyMemberSettings(Base):
    """Family member settings model."""
    
    __tablename__ = "family_member_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False, unique=True)
    show_accounts = Column(Boolean, default=True, nullable=False)
    default_visibility = Column(String(50), default="full", nullable=False)  # 'full' or 'limited'
    custom_limits = Column(JSON, nullable=True)  # Additional custom settings
    
    # Relationships
    member = relationship("FamilyMember", back_populates="settings")
    
    def __repr__(self):
        return f"<FamilyMemberSettings(member_id={self.member_id})>"


class FamilySharedAccount(Base):
    """Shared accounts for family members."""
    
    __tablename__ = "family_shared_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    visibility = Column(SQLEnum(AccountVisibility), default=AccountVisibility.FAMILY, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    family = relationship("FamilyGroup")
    member = relationship("FamilyMember")
    # Note: Account relationship would be from app.models.account import Account
    
    def __repr__(self):
        return f"<FamilySharedAccount(family_id={self.family_id}, member_id={self.member_id}, account_id={self.account_id})>"


class FamilyBudget(Base):
    """Family budget model."""
    
    __tablename__ = "family_budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    period = Column(SQLEnum(FamilyBudgetPeriod, values_callable=lambda x: [e.value for e in x]), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    family = relationship("FamilyGroup", back_populates="budgets")
    category = relationship("Category")
    
    def __repr__(self):
        return f"<FamilyBudget(id={self.id}, family_id={self.family_id}, name='{self.name}', amount={self.amount})>"


class FamilyMemberLimit(Base):
    """Family member spending limit model."""
    
    __tablename__ = "family_member_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    period = Column(SQLEnum(FamilyBudgetPeriod, values_callable=lambda x: [e.value for e in x]), nullable=False)
    auto_unlock = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    family = relationship("FamilyGroup", back_populates="limits")
    member = relationship("FamilyMember", back_populates="limits")
    category = relationship("Category")
    
    def __repr__(self):
        return f"<FamilyMemberLimit(id={self.id}, member_id={self.member_id}, amount={self.amount})>"


class FamilyGoal(Base):
    """Family goal model."""
    
    __tablename__ = "family_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_amount = Column(Numeric(15, 2), nullable=False)
    current_amount = Column(Numeric(15, 2), default=0, nullable=False)
    deadline = Column(DateTime, nullable=True)
    status = Column(SQLEnum(FamilyGoalStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FamilyGoalStatus.ACTIVE)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    family = relationship("FamilyGroup", back_populates="goals")
    creator = relationship("User", foreign_keys=[created_by])
    contributions = relationship("FamilyGoalContribution", back_populates="goal", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FamilyGoal(id={self.id}, name='{self.name}', target={self.target_amount}, current={self.current_amount})>"


class FamilyGoalContribution(Base):
    """Family goal contribution model."""
    
    __tablename__ = "family_goal_contributions"
    
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("family_goals.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    source_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    scheduled = Column(Boolean, default=False, nullable=False)
    schedule_rule = Column(JSON, nullable=True)  # For recurring contributions
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    goal = relationship("FamilyGoal", back_populates="contributions")
    member = relationship("FamilyMember")
    source_account = relationship("Account")
    
    def __repr__(self):
        return f"<FamilyGoalContribution(id={self.id}, goal_id={self.goal_id}, amount={self.amount})>"


class FamilyTransfer(Base):
    """Family internal transfer model."""
    
    __tablename__ = "family_transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    from_member_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False)
    to_member_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False)
    from_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="RUB", nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(FamilyTransferStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FamilyTransferStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    family = relationship("FamilyGroup", back_populates="transfers")
    from_member = relationship("FamilyMember", foreign_keys=[from_member_id])
    to_member = relationship("FamilyMember", foreign_keys=[to_member_id])
    from_account = relationship("Account", foreign_keys=[from_account_id])
    to_account = relationship("Account", foreign_keys=[to_account_id])
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<FamilyTransfer(id={self.id}, from={self.from_member_id}, to={self.to_member_id}, amount={self.amount}, status={self.status})>"


class FamilyNotification(Base):
    """Family notification model."""
    
    __tablename__ = "family_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True, index=True)  # null = all members
    type = Column(SQLEnum(FamilyNotificationType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    payload = Column(JSON, nullable=False)  # Additional data
    status = Column(String(50), default="new", nullable=False)  # 'new', 'read'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    family = relationship("FamilyGroup", back_populates="notifications")
    member = relationship("FamilyMember")
    
    def __repr__(self):
        return f"<FamilyNotification(id={self.id}, type={self.type}, status={self.status})>"


class FamilyActivityLog(Base):
    """Family activity log model for audit trail."""
    
    __tablename__ = "family_activity_log"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # 'created_budget', 'set_limit', 'approved_transfer', etc.
    target = Column(String(100), nullable=True)  # Target entity type
    action_metadata = Column(JSON, nullable=True)  # Additional context (renamed from metadata)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    family = relationship("FamilyGroup", back_populates="activity_logs")
    actor = relationship("User")
    
    def __repr__(self):
        return f"<FamilyActivityLog(id={self.id}, action='{self.action}', timestamp={self.timestamp})>"

