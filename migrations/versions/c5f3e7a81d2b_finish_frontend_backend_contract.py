"""finish frontend backend contract

Revision ID: c5f3e7a81d2b
Revises: 2e42daaaadb6
Create Date: 2026-09-12 01:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c5f3e7a81d2b"
down_revision: str | None = "2e42daaaadb6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_application_program_creator", "creator_applications", type_="unique")
    op.create_index(
        "uq_application_active_program_creator",
        "creator_applications",
        ["program_id", "creator_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('submitted', 'in_review')"),
    )

    op.add_column("creator_invitations", sa.Column("created_by", sa.Uuid(), nullable=True))
    op.add_column("creator_invitations", sa.Column("revoked_at", sa.DateTime(timezone=True)))
    op.add_column("creator_invitations", sa.Column("accepted_by", sa.Uuid(), nullable=True))
    op.add_column("creator_invitations", sa.Column("application_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_creator_invitations_created_by_users",
        "creator_invitations",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_creator_invitations_accepted_by_users",
        "creator_invitations",
        "users",
        ["accepted_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_creator_invitations_application_id_creator_applications",
        "creator_invitations",
        "creator_applications",
        ["application_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_creator_invitations_application_id", "creator_invitations", ["application_id"]
    )

    op.create_table(
        "campaign_participants",
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "selected",
                "removed",
                name="campaign_participant_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("selected_by", sa.Uuid(), nullable=True),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["membership_id"], ["program_memberships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["selected_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "membership_id", name="uq_campaign_participant"),
    )
    op.create_index(
        "ix_campaign_participant_status",
        "campaign_participants",
        ["campaign_id", "status"],
    )

    op.create_index(
        "uq_asset_membership_program_type",
        "affiliate_assets",
        ["membership_id", "asset_type"],
        unique=True,
        postgresql_where=sa.text("campaign_id IS NULL"),
    )
    op.create_index(
        "uq_asset_membership_campaign_type",
        "affiliate_assets",
        ["membership_id", "campaign_id", "asset_type"],
        unique=True,
        postgresql_where=sa.text("campaign_id IS NOT NULL"),
    )

    op.drop_constraint("uq_content_network_external", "content_evidence", type_="unique")
    op.create_unique_constraint(
        "uq_content_brand_network_external",
        "content_evidence",
        ["brand_id", "network", "external_post_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_content_brand_network_external", "content_evidence", type_="unique")
    op.create_unique_constraint(
        "uq_content_network_external", "content_evidence", ["network", "external_post_id"]
    )
    op.drop_index("uq_asset_membership_campaign_type", table_name="affiliate_assets")
    op.drop_index("uq_asset_membership_program_type", table_name="affiliate_assets")
    op.drop_index("ix_campaign_participant_status", table_name="campaign_participants")
    op.drop_table("campaign_participants")
    op.drop_constraint(
        "uq_creator_invitations_application_id", "creator_invitations", type_="unique"
    )
    op.drop_constraint(
        "fk_creator_invitations_application_id_creator_applications",
        "creator_invitations",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_creator_invitations_accepted_by_users", "creator_invitations", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_creator_invitations_created_by_users", "creator_invitations", type_="foreignkey"
    )
    op.drop_column("creator_invitations", "application_id")
    op.drop_column("creator_invitations", "accepted_by")
    op.drop_column("creator_invitations", "revoked_at")
    op.drop_column("creator_invitations", "created_by")
    op.drop_index("uq_application_active_program_creator", table_name="creator_applications")
    op.create_unique_constraint(
        "uq_application_program_creator",
        "creator_applications",
        ["program_id", "creator_id"],
    )
