"""Add family hub module tables.

Revision ID: 20251106_1500
Revises: 20251106_0235_fix_all_enums
Create Date: 2025-11-06 15:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20251106_1500"
down_revision = "20251106_0235_fix_all_enums"
branch_labels = None
depends_on = None


def upgrade() -> None:
    familyrole = sa.Enum("admin", "member", name="familyrole")
    familymemberstatus = sa.Enum("pending", "active", "blocked", name="familymemberstatus")
    familybudgetperiod = sa.Enum("weekly", "monthly", name="familybudgetperiod")
    familybudgetstatus = sa.Enum("active", "archived", "cancelled", name="familybudgetstatus")
    familymemberlimitperiod = sa.Enum("weekly", "monthly", name="familymemberlimitperiod")
    familymemberlimitstatus = sa.Enum("active", "suspended", "archived", name="familymemberlimitstatus")
    familygoalstatus = sa.Enum("active", "completed", "archived", name="familygoalstatus")
    familytransferstatus = sa.Enum(
        "pending",
        "approved",
        "rejected",
        "executed",
        "failed",
        "cancelled",
        name="familytransferstatus",
    )
    familynotificationtype = sa.Enum(
        "limit_approach",
        "limit_exceeded",
        "budget_approach",
        "transfer_request",
        "transfer_approved",
        "goal_progress",
        "goal_completed",
        name="familynotificationtype",
    )
    familynotificationstatus = sa.Enum("new", "read", "archived", name="familynotificationstatus")
    accountvisibilityscope = sa.Enum("family", "private", name="accountvisibilityscope")

    familyrole.create(op.get_bind(), checkfirst=True)
    familymemberstatus.create(op.get_bind(), checkfirst=True)
    familybudgetperiod.create(op.get_bind(), checkfirst=True)
    familybudgetstatus.create(op.get_bind(), checkfirst=True)
    familymemberlimitperiod.create(op.get_bind(), checkfirst=True)
    familymemberlimitstatus.create(op.get_bind(), checkfirst=True)
    familygoalstatus.create(op.get_bind(), checkfirst=True)
    familytransferstatus.create(op.get_bind(), checkfirst=True)
    familynotificationtype.create(op.get_bind(), checkfirst=True)
    familynotificationstatus.create(op.get_bind(), checkfirst=True)
    accountvisibilityscope.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "family_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("invite_code", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_family_groups_id"), "family_groups", ["id"], unique=False)
    op.create_index(op.f("ix_family_groups_invite_code"), "family_groups", ["invite_code"], unique=True)

    op.create_table(
        "family_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", familyrole, nullable=False, server_default="member"),
        sa.Column("status", familymemberstatus, nullable=False, server_default="pending"),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["family_id"], ["family_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "user_id", name="uq_family_member"),
    )
    op.create_index(op.f("ix_family_members_id"), "family_members", ["id"], unique=False)

    op.create_table(
        "family_member_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("show_accounts", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("default_visibility", sa.String(length=32), nullable=False, server_default="family"),
        sa.Column("custom_limits", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["member_id"], ["family_members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("member_id"),
    )

    op.create_table(
        "family_budgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("period", familybudgetperiod, nullable=False),
        sa.Column("status", familybudgetstatus, nullable=False, server_default="active"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_by_member_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_member_id"], ["family_members.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["family_id"], ["family_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_family_budgets_id"), "family_budgets", ["id"], unique=False)

    op.create_table(
        "family_member_limits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("period", familymemberlimitperiod, nullable=False),
        sa.Column("status", familymemberlimitstatus, nullable=False, server_default="active"),
        sa.Column("auto_unlock", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reset_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["family_id"], ["family_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["family_members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_family_member_limits_id"), "family_member_limits", ["id"], unique=False)

    op.create_table(
        "family_goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("current_amount", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("status", familygoalstatus, nullable=False, server_default="active"),
        sa.Column("created_by_member_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["created_by_member_id"], ["family_members.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["family_id"], ["family_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_family_goals_id"), "family_goals", ["id"], unique=False)

    op.create_table(
        "family_goal_contributions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("source_account_id", sa.Integer(), nullable=True),
        sa.Column("scheduled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("schedule_rule", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["goal_id"], ["family_goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["family_members.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_family_goal_contributions_id"), "family_goal_contributions", ["id"], unique=False)

    op.create_table(
        "family_transfers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("from_member_id", sa.Integer(), nullable=True),
        sa.Column("to_member_id", sa.Integer(), nullable=True),
        sa.Column("from_account_id", sa.Integer(), nullable=True),
        sa.Column("to_account_id", sa.Integer(), nullable=True),
        sa.Column("requested_by_member_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_member_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="RUB"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", familytransferstatus, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["approved_by_member_id"], ["family_members.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["family_id"], ["family_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["from_member_id"], ["family_members.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requested_by_member_id"], ["family_members.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_member_id"], ["family_members.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_family_transfers_id"), "family_transfers", ["id"], unique=False)

    op.create_table(
        "family_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=True),
        sa.Column("notification_type", familynotificationtype, nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("status", familynotificationstatus, nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["family_id"], ["family_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["family_members.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_family_notifications_id"), "family_notifications", ["id"], unique=False)

    op.create_table(
        "family_activity_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("actor_member_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target_type", sa.String(length=128), nullable=True),
        sa.Column("target_id", sa.String(length=128), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["actor_member_id"], ["family_members.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["family_id"], ["family_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_family_activity_log_id"), "family_activity_log", ["id"], unique=False)

    op.create_table(
        "family_account_visibility",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("visibility_scope", sa.String(length=32), nullable=False, server_default="family"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["family_id"], ["family_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "account_id", name="uq_family_account_visibility"),
    )

    op.add_column(
        "accounts",
        sa.Column("primary_family_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "accounts",
        sa.Column("visibility_scope", accountvisibilityscope, nullable=False, server_default="family"),
    )
    op.create_foreign_key(
        "fk_accounts_primary_family",
        "accounts",
        "family_groups",
        ["primary_family_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_accounts_primary_family", "accounts", type_="foreignkey")
    op.drop_column("accounts", "visibility_scope")
    op.drop_column("accounts", "primary_family_id")

    op.drop_table("family_account_visibility")
    op.drop_index(op.f("ix_family_activity_log_id"), table_name="family_activity_log")
    op.drop_table("family_activity_log")
    op.drop_index(op.f("ix_family_notifications_id"), table_name="family_notifications")
    op.drop_table("family_notifications")
    op.drop_index(op.f("ix_family_transfers_id"), table_name="family_transfers")
    op.drop_table("family_transfers")
    op.drop_index(op.f("ix_family_goal_contributions_id"), table_name="family_goal_contributions")
    op.drop_table("family_goal_contributions")
    op.drop_index(op.f("ix_family_goals_id"), table_name="family_goals")
    op.drop_table("family_goals")
    op.drop_index(op.f("ix_family_member_limits_id"), table_name="family_member_limits")
    op.drop_table("family_member_limits")
    op.drop_index(op.f("ix_family_budgets_id"), table_name="family_budgets")
    op.drop_table("family_budgets")
    op.drop_table("family_member_settings")
    op.drop_index(op.f("ix_family_members_id"), table_name="family_members")
    op.drop_table("family_members")
    op.drop_index(op.f("ix_family_groups_invite_code"), table_name="family_groups")
    op.drop_index(op.f("ix_family_groups_id"), table_name="family_groups")
    op.drop_table("family_groups")

    bind = op.get_bind()
    accountvisibilityscope = sa.Enum(name="accountvisibilityscope")
    familynotificationstatus = sa.Enum(name="familynotificationstatus")
    familynotificationtype = sa.Enum(name="familynotificationtype")
    familytransferstatus = sa.Enum(name="familytransferstatus")
    familygoalstatus = sa.Enum(name="familygoalstatus")
    familymemberlimitstatus = sa.Enum(name="familymemberlimitstatus")
    familymemberlimitperiod = sa.Enum(name="familymemberlimitperiod")
    familybudgetstatus = sa.Enum(name="familybudgetstatus")
    familybudgetperiod = sa.Enum(name="familybudgetperiod")
    familymemberstatus = sa.Enum(name="familymemberstatus")
    familyrole = sa.Enum(name="familyrole")

    accountvisibilityscope.drop(bind, checkfirst=True)
    familynotificationstatus.drop(bind, checkfirst=True)
    familynotificationtype.drop(bind, checkfirst=True)
    familytransferstatus.drop(bind, checkfirst=True)
    familygoalstatus.drop(bind, checkfirst=True)
    familymemberlimitstatus.drop(bind, checkfirst=True)
    familymemberlimitperiod.drop(bind, checkfirst=True)
    familybudgetstatus.drop(bind, checkfirst=True)
    familybudgetperiod.drop(bind, checkfirst=True)
    familymemberstatus.drop(bind, checkfirst=True)
    familyrole.drop(bind, checkfirst=True)

