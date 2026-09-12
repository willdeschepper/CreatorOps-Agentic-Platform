import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from creatorops.core.db import Base
from creatorops.models.common import TimestampMixin, UUIDPrimaryKeyMixin, enum_type
from creatorops.models.enums import (
    AttributionReason,
    CommerceEventType,
    OrderStatus,
    WebhookProcessingStatus,
)


class AffiliateClick(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "affiliate_clicks"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("affiliate_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    visitor_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    ip_hash: Mapped[str | None] = mapped_column(String(64))


class CommerceWebhookEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "commerce_webhook_events"
    __table_args__ = (
        UniqueConstraint(
            "brand_id", "provider", "external_event_id", name="uq_webhook_brand_provider_event"
        ),
        Index("ix_webhook_received_at", "received_at"),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="local-commerce")
    external_event_id: Mapped[str] = mapped_column(String(160), nullable=False)
    event_type: Mapped[CommerceEventType] = mapped_column(
        enum_type(CommerceEventType, "commerce_event_type"), nullable=False
    )
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[WebhookProcessingStatus] = mapped_column(
        enum_type(WebhookProcessingStatus, "webhook_processing_status"),
        nullable=False,
        default=WebhookProcessingStatus.RECEIVED,
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"))
    response: Mapped[dict[str, object] | None] = mapped_column(JSONB)


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("brand_id", "external_id", name="uq_order_brand_external"),
        Index("ix_orders_brand_status", "brand_id", "status"),
        CheckConstraint("gross_amount > 0", name="order_gross_positive"),
        CheckConstraint("refunded_amount >= 0", name="order_refund_non_negative"),
        CheckConstraint("refunded_amount <= gross_amount", name="order_refund_within_gross"),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("programs.id", ondelete="SET NULL"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        enum_type(OrderStatus, "order_status"), nullable=False, default=OrderStatus.CREATED
    )
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    refunded_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OrderAttribution(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "order_attributions"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("program_memberships.id", ondelete="SET NULL"), index=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL")
    )
    coupon_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("affiliate_assets.id", ondelete="SET NULL")
    )
    click_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("affiliate_clicks.id", ondelete="SET NULL")
    )
    reason: Mapped[AttributionReason] = mapped_column(
        enum_type(AttributionReason, "attribution_reason"), nullable=False
    )
    signals: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    attributed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
