import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from creatorops.core.db import Base
from creatorops.models.common import UUIDPrimaryKeyMixin, enum_type
from creatorops.models.enums import (
    FindingState,
    FindingType,
    GateResult,
    ProposalAction,
    ProposalState,
    ReconciliationRunStatus,
)


class ReconciliationRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reconciliation_runs"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    started_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[ReconciliationRunStatus] = mapped_column(
        enum_type(ReconciliationRunStatus, "reconciliation_run_status"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)


class Finding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "agent_findings"
    __table_args__ = (
        Index("ix_finding_brand_state", "brand_id", "state"),
        UniqueConstraint("payout_id", "finding_type", "evidence_hash", name="uq_finding_evidence"),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reconciliation_runs.id", ondelete="RESTRICT"), nullable=False
    )
    payout_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payouts.id", ondelete="RESTRICT"), nullable=False
    )
    finding_type: Mapped[FindingType] = mapped_column(
        enum_type(FindingType, "finding_type"), nullable=False
    )
    state: Mapped[FindingState] = mapped_column(
        enum_type(FindingState, "finding_state"),
        nullable=False,
        default=FindingState.OPEN,
    )
    evidence: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payout_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Proposal(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "agent_proposals"
    __table_args__ = (Index("ix_proposal_finding_state", "finding_id", "state"),)

    finding_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_findings.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[ProposalAction] = mapped_column(
        enum_type(ProposalAction, "proposal_action"), nullable=False
    )
    state: Mapped[ProposalState] = mapped_column(
        enum_type(ProposalState, "proposal_state"),
        nullable=False,
        default=ProposalState.DRAFT,
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    risk: Mapped[str] = mapped_column(String(40), nullable=False)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payout_version: Mapped[int] = mapped_column(Integer, nullable=False)
    proposed_changes: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    approval_comment: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    rejection_comment: Mapped[str | None] = mapped_column(Text)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GateRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "agent_gate_runs"

    proposal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_proposals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    result: Mapped[GateResult] = mapped_column(enum_type(GateResult, "gate_result"), nullable=False)
    checks: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
