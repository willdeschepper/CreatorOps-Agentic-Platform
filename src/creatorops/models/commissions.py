import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from creatorops.core.db import Base
from creatorops.models.common import TimestampMixin, UUIDPrimaryKeyMixin, enum_type
from creatorops.models.enums import (
    CommissionKind,
    CommissionMetric,
    CommissionStatus,
    LedgerBucket,
    LedgerEntryType,
)


class CommissionPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commission_plans"
    __table_args__ = (
        UniqueConstraint(
            "program_id", "campaign_id", "version", name="uq_commission_plan_scope_version"
        ),
        Index("ix_commission_plan_active", "program_id", "campaign_id", "active_from"),
        CheckConstraint("base_rate >= 0 AND base_rate <= 1", name="base_rate_valid"),
        CheckConstraint("return_window_days >= 0", name="plan_return_window_non_negative"),
        CheckConstraint("payout_minimum > 0", name="plan_payout_minimum_positive"),
    )

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE")
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    base_rate: Mapped[Decimal] = mapped_column(Numeric(7, 6), nullable=False)
    return_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    payout_minimum: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CommissionTier(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "commission_tiers"
    __table_args__ = (
        UniqueConstraint("plan_id", "threshold_gmv", name="uq_commission_tier_threshold"),
        CheckConstraint("threshold_gmv >= 0", name="tier_threshold_non_negative"),
        CheckConstraint("rate >= 0 AND rate <= 1", name="tier_rate_valid"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("commission_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    threshold_gmv: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(7, 6), nullable=False)


class BonusRule(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "bonus_rules"
    __table_args__ = (
        CheckConstraint("threshold > 0", name="bonus_threshold_positive"),
        CheckConstraint("amount > 0", name="bonus_amount_positive"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("commission_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    metric: Mapped[CommissionMetric] = mapped_column(
        enum_type(CommissionMetric, "commission_metric"), nullable=False
    )
    threshold: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


class Commission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commissions"
    __table_args__ = (
        UniqueConstraint("order_id", "kind", "bonus_rule_id", name="uq_commission_order_kind_rule"),
        UniqueConstraint(
            "membership_id", "bonus_rule_id", "period_key", name="uq_commission_bonus_period"
        ),
        Index(
            "uq_commission_sale_order",
            "order_id",
            unique=True,
            postgresql_where=text("kind = 'sale'"),
        ),
        Index(
            "uq_commission_adjustment_source",
            "source_event_id",
            "adjustment_of_id",
            unique=True,
            postgresql_where=text("kind = 'refund_adjustment'"),
        ),
        Index("ix_commission_membership_status", "membership_id", "status"),
        CheckConstraint("rate >= 0 AND rate <= 1", name="commission_rate_valid"),
        CheckConstraint("length(period_key) = 7", name="commission_period_key_length"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_memberships.id", ondelete="RESTRICT"), nullable=False
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("commission_plans.id", ondelete="RESTRICT"), nullable=False
    )
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bonus_rules.id", ondelete="RESTRICT")
    )
    adjustment_of_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("commissions.id", ondelete="RESTRICT")
    )
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("commerce_webhook_events.id", ondelete="RESTRICT")
    )
    kind: Mapped[CommissionKind] = mapped_column(
        enum_type(CommissionKind, "commission_kind"), nullable=False
    )
    status: Mapped[CommissionStatus] = mapped_column(
        enum_type(CommissionStatus, "commission_status"), nullable=False
    )
    gross_basis: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(7, 6), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    period_key: Mapped[str] = mapped_column(String(7), nullable=False)
    eligible_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LedgerEntry(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_ledger_idempotency_key"),
        Index("ix_ledger_membership_bucket", "membership_id", "bucket"),
        Index("ix_ledger_program_created", "program_id", "created_at"),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="RESTRICT"), nullable=False
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_memberships.id", ondelete="RESTRICT"), nullable=False
    )
    commission_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("commissions.id", ondelete="RESTRICT")
    )
    payout_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payouts.id", ondelete="RESTRICT")
    )
    bucket: Mapped[LedgerBucket] = mapped_column(
        enum_type(LedgerBucket, "ledger_bucket"), nullable=False
    )
    entry_type: Mapped[LedgerEntryType] = mapped_column(
        enum_type(LedgerEntryType, "ledger_entry_type"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
