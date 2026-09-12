import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from creatorops.core.db import Base
from creatorops.models.common import TimestampMixin, UUIDPrimaryKeyMixin, enum_type
from creatorops.models.enums import (
    ApplicationSource,
    ApplicationStatus,
    AssetType,
    CampaignParticipantStatus,
    InvitationStatus,
    MembershipStatus,
)


class CreatorApplication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "creator_applications"
    __table_args__ = (
        Index(
            "uq_application_active_program_creator",
            "program_id",
            "creator_id",
            unique=True,
            postgresql_where=text("status IN ('submitted', 'in_review')"),
        ),
        Index("ix_application_program_status", "program_id", "status"),
    )

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[ApplicationSource] = mapped_column(
        enum_type(ApplicationSource, "application_source"),
        nullable=False,
        default=ApplicationSource.SELF,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        enum_type(ApplicationStatus, "application_status"),
        nullable=False,
        default=ApplicationStatus.SUBMITTED,
    )
    motivation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CreatorInvitation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "creator_invitations"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_invitation_token_hash"),)

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[InvitationStatus] = mapped_column(
        enum_type(InvitationStatus, "invitation_status"),
        nullable=False,
        default=InvitationStatus.PENDING,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("creator_applications.id", ondelete="SET NULL"), unique=True
    )


class ProgramMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "program_memberships"
    __table_args__ = (
        UniqueConstraint("program_id", "creator_id", name="uq_membership_program_creator"),
        Index("ix_membership_program_status", "program_id", "status"),
    )

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("creator_applications.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    status: Mapped[MembershipStatus] = mapped_column(
        enum_type(MembershipStatus, "membership_status"),
        nullable=False,
        default=MembershipStatus.AWAITING_TERMS,
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(nullable=False, default=1)


class CampaignParticipant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaign_participants"
    __table_args__ = (
        UniqueConstraint("campaign_id", "membership_id", name="uq_campaign_participant"),
        Index("ix_campaign_participant_status", "campaign_id", "status"),
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_memberships.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[CampaignParticipantStatus] = mapped_column(
        enum_type(CampaignParticipantStatus, "campaign_participant_status"),
        nullable=False,
        default=CampaignParticipantStatus.SELECTED,
    )
    selected_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(nullable=False, default=1)


class TermsAcceptance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "terms_acceptances"
    __table_args__ = (UniqueConstraint("membership_id", "terms_id", name="uq_terms_acceptance"),)

    membership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_memberships.id", ondelete="CASCADE"), nullable=False
    )
    terms_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_terms.id", ondelete="RESTRICT"), nullable=False
    )
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(500))


class AffiliateAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "affiliate_assets"
    __table_args__ = (
        UniqueConstraint("asset_type", "code", name="uq_affiliate_asset_type_code"),
        Index(
            "uq_asset_membership_program_type",
            "membership_id",
            "asset_type",
            unique=True,
            postgresql_where=text("campaign_id IS NULL"),
        ),
        Index(
            "uq_asset_membership_campaign_type",
            "membership_id",
            "campaign_id",
            "asset_type",
            unique=True,
            postgresql_where=text("campaign_id IS NOT NULL"),
        ),
        Index("ix_affiliate_assets_membership", "membership_id", "active"),
    )

    membership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_memberships.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL")
    )
    asset_type: Mapped[AssetType] = mapped_column(
        enum_type(AssetType, "affiliate_asset_type"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    target_url: Mapped[str | None] = mapped_column(String(1000))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
