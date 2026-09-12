import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from creatorops.core.db import Base
from creatorops.models.common import TimestampMixin, UUIDPrimaryKeyMixin, enum_type
from creatorops.models.enums import ContentStatus, SocialNetwork


class ContentEvidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_evidence"
    __table_args__ = (
        UniqueConstraint(
            "brand_id",
            "network",
            "external_post_id",
            name="uq_content_brand_network_external",
        ),
        Index("ix_content_brand_status", "brand_id", "status"),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL")
    )
    membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("program_memberships.id", ondelete="SET NULL")
    )
    network: Mapped[SocialNetwork] = mapped_column(
        enum_type(SocialNetwork, "content_social_network"), nullable=False
    )
    external_post_id: Mapped[str] = mapped_column(String(160), nullable=False)
    firestore_path: Mapped[str] = mapped_column(String(500), nullable=False)
    handle_normalized: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[ContentStatus] = mapped_column(
        enum_type(ContentStatus, "content_status"), nullable=False
    )
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metrics: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
