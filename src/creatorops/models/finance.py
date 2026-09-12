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
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from creatorops.core.db import Base
from creatorops.models.common import TimestampMixin, UUIDPrimaryKeyMixin, enum_type
from creatorops.models.enums import PayoutBatchStatus, PayoutStatus, ProviderScenario


class PayoutBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payout_batches"
    __table_args__ = (Index("ix_payout_batch_program_status", "program_id", "status"),)

    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="RESTRICT"), nullable=False
    )
    cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[PayoutBatchStatus] = mapped_column(
        enum_type(PayoutBatchStatus, "payout_batch_status"),
        nullable=False,
        default=PayoutBatchStatus.DRAFT,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    approval_comment: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Payout(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payouts"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_payout_idempotency_key"),
        UniqueConstraint("provider_reference", name="uq_payout_provider_reference"),
        UniqueConstraint("batch_id", "membership_id", name="uq_payout_batch_membership"),
        Index("ix_payout_brand_status", "brand_id", "status"),
        CheckConstraint("amount > 0", name="payout_amount_positive"),
        CheckConstraint("version >= 1", name="payout_version_positive"),
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payout_batches.id", ondelete="RESTRICT"), nullable=False
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
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    status: Mapped[PayoutStatus] = mapped_column(
        enum_type(PayoutStatus, "payout_status"), nullable=False, default=PayoutStatus.DRAFT
    )
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(160))
    simulation_scenario: Mapped[ProviderScenario] = mapped_column(
        enum_type(ProviderScenario, "provider_scenario"),
        nullable=False,
        default=ProviderScenario.SUCCESS,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reserved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    unknown_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
