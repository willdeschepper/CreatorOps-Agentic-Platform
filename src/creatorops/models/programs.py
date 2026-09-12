import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from creatorops.core.db import Base
from creatorops.models.common import TimestampMixin, UUIDPrimaryKeyMixin, enum_type
from creatorops.models.enums import CampaignStatus, ProgramStatus


class Program(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "programs"
    __table_args__ = (
        UniqueConstraint("brand_id", "slug", name="uq_program_brand_slug"),
        CheckConstraint("attribution_window_days > 0", name="attribution_window_positive"),
        CheckConstraint("return_window_days >= 0", name="return_window_non_negative"),
        CheckConstraint("payout_minimum > 0", name="payout_minimum_positive"),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ProgramStatus] = mapped_column(
        enum_type(ProgramStatus, "program_status"), nullable=False, default=ProgramStatus.DRAFT
    )
    attribution_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    return_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    payout_minimum: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("100.00")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")


class ProgramTerms(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "program_terms"
    __table_args__ = (UniqueConstraint("program_id", "version", name="uq_program_terms_version"),)

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    required: Mapped[bool] = mapped_column(nullable=False, default=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        UniqueConstraint("program_id", "name", name="uq_campaign_program_name"),
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="campaign_dates_ordered",
        ),
    )

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        enum_type(CampaignStatus, "campaign_status"),
        nullable=False,
        default=CampaignStatus.DRAFT,
    )
    briefing: Mapped[str] = mapped_column(Text, nullable=False, default="")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
