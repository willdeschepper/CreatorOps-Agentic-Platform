import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from creatorops.core.db import Base
from creatorops.models.common import TimestampMixin, UUIDPrimaryKeyMixin, enum_type
from creatorops.models.enums import BrandRole, SocialNetwork, UserKind


class Brand(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="America/Sao_Paulo")


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    kind: Mapped[UserKind] = mapped_column(enum_type(UserKind, "user_kind"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BrandMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "brand_memberships"
    __table_args__ = (
        UniqueConstraint("brand_id", "user_id", name="uq_brand_membership_brand_user"),
        Index("ix_brand_memberships_user", "user_id"),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[BrandRole] = mapped_column(enum_type(BrandRole, "brand_role"), nullable=False)


class SocialProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "social_profiles"
    __table_args__ = (
        UniqueConstraint("network", "handle_normalized", name="uq_social_network_handle"),
        UniqueConstraint("creator_id", "network", name="uq_creator_social_network"),
    )

    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    network: Mapped[SocialNetwork] = mapped_column(
        enum_type(SocialNetwork, "social_network"), nullable=False
    )
    handle: Mapped[str] = mapped_column(String(120), nullable=False)
    handle_normalized: Mapped[str] = mapped_column(String(120), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
