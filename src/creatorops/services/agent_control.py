import hashlib
import json
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.config import settings
from creatorops.core.db import session_factory
from creatorops.core.errors import ConflictError, NotFoundError
from creatorops.core.security import Principal
from creatorops.core.time import clock
from creatorops.models.agent_control import Finding, GateRun, Proposal, ReconciliationRun
from creatorops.models.commissions import LedgerEntry
from creatorops.models.enums import (
    FindingState,
    FindingType,
    GateResult,
    LedgerBucket,
    PayoutStatus,
    ProposalAction,
    ProposalState,
    ReconciliationRunStatus,
)
from creatorops.models.finance import Payout
from creatorops.models.partnerships import ProgramMembership
from creatorops.services.finance import _apply_provider_result
from creatorops.services.provider import PayoutProvider, ProviderTransfer, provider
from creatorops.services.shared import add_audit, enqueue_event


def evidence_hash(evidence: dict[str, object]) -> str:
    encoded = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


async def _reserved_for_payout(session: AsyncSession, payout_id: uuid.UUID) -> Decimal:
    amount = await session.scalar(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.payout_id == payout_id,
            LedgerEntry.bucket == LedgerBucket.RESERVED,
        )
    )
    return Decimal(amount or 0)


def _provider_payload(transfer: ProviderTransfer | None) -> dict[str, object] | None:
    if transfer is None:
        return None
    return {
        "provider_reference": transfer.provider_reference,
        "idempotency_key": transfer.idempotency_key,
        "payout_id": str(transfer.payout_id),
        "beneficiary_id": str(transfer.beneficiary_id),
        "amount": str(transfer.amount),
        "currency": transfer.currency,
        "status": transfer.status,
    }


async def run_reconciliation(
    *,
    brand_id: uuid.UUID,
    started_by: uuid.UUID,
    payout_provider: PayoutProvider = provider,
) -> tuple[ReconciliationRun, list[Finding]]:
    now = clock.now()
    async with session_factory() as session, session.begin():
        run = ReconciliationRun(
            brand_id=brand_id,
            started_by=started_by,
            status=ReconciliationRunStatus.RUNNING,
            started_at=now,
            summary={},
        )
        session.add(run)
        await session.flush()
        run_id = run.id

    async with session_factory() as session:
        payouts = list(
            (
                await session.scalars(
                    select(Payout).where(
                        Payout.brand_id == brand_id,
                        Payout.status.in_([PayoutStatus.PENDING, PayoutStatus.UNKNOWN]),
                    )
                )
            ).all()
        )

    candidates: list[tuple[Payout, FindingType, dict[str, object]]] = []
    for payout in payouts:
        if payout.status == PayoutStatus.PENDING and payout.updated_at > now - timedelta(
            seconds=settings.reconciliation_unknown_after_seconds
        ):
            continue
        external = await payout_provider.find_by_key(payout.idempotency_key)
        statement = await payout_provider.statement(payout.id)
        async with session_factory() as balance_session:
            reserved = await _reserved_for_payout(balance_session, payout.id)
        evidence: dict[str, object] = {
            "payout_id": str(payout.id),
            "brand_id": str(payout.brand_id),
            "membership_id": str(payout.membership_id),
            "internal_status": payout.status.value,
            "internal_amount": str(payout.amount),
            "currency": payout.currency,
            "idempotency_key": payout.idempotency_key,
            "payout_version": payout.version,
            "reserved_balance": str(reserved),
            "provider": _provider_payload(external),
            "provider_transfer_count": len(statement),
        }
        finding_type: FindingType | None = None
        if len(statement) > 1:
            finding_type = FindingType.DUPLICATE_PROVIDER_TRANSFER
        elif external and (
            external.amount != payout.amount or external.currency != payout.currency
        ):
            finding_type = FindingType.AMOUNT_MISMATCH
        elif (
            external
            and external.status == "confirmed"
            and payout.status
            in {
                PayoutStatus.PENDING,
                PayoutStatus.UNKNOWN,
            }
        ):
            finding_type = FindingType.PROVIDER_CONFIRMED_INTERNAL_UNKNOWN
        elif external is None and payout.status == PayoutStatus.UNKNOWN:
            finding_type = FindingType.PROVIDER_MISSING_INTERNAL_UNKNOWN
        elif reserved != payout.amount:
            finding_type = FindingType.LEDGER_BALANCE_MISMATCH
        if finding_type:
            candidates.append((payout, finding_type, evidence))

    findings: list[Finding] = []
    created_findings = 0
    async with session_factory() as session, session.begin():
        for payout_snapshot, finding_type, evidence in candidates:
            digest = evidence_hash(evidence)
            existing = await session.scalar(
                select(Finding).where(
                    Finding.payout_id == payout_snapshot.id,
                    Finding.finding_type == finding_type,
                    Finding.evidence_hash == digest,
                )
            )
            if existing:
                findings.append(existing)
                continue
            finding = Finding(
                brand_id=brand_id,
                run_id=run_id,
                payout_id=payout_snapshot.id,
                finding_type=finding_type,
                state=FindingState.OPEN,
                evidence=evidence,
                evidence_hash=digest,
                payout_version=payout_snapshot.version,
                created_at=now,
            )
            session.add(finding)
            findings.append(finding)
            created_findings += 1
        completed_run = await session.get(ReconciliationRun, run_id)
        assert completed_run is not None
        completed_run.status = ReconciliationRunStatus.COMPLETED
        completed_run.completed_at = clock.now()
        completed_run.summary = {
            "payouts_scanned": len(payouts),
            "findings": len(findings),
            "new_findings": created_findings,
        }
    return completed_run, findings


async def list_findings(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    state: FindingState | None = None,
) -> list[Finding]:
    statement = select(Finding).where(Finding.brand_id == brand_id)
    if state:
        statement = statement.where(Finding.state == state)
    return list((await session.scalars(statement.order_by(Finding.created_at.desc()))).all())


async def generate_proposal(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    finding_id: uuid.UUID,
) -> Proposal:
    now = clock.now()
    async with session.begin():
        finding = await session.scalar(
            select(Finding)
            .where(Finding.id == finding_id, Finding.brand_id == brand_id)
            .with_for_update()
        )
        if finding is None:
            raise NotFoundError("finding_not_found", "Finding was not found")
        existing = await session.scalar(
            select(Proposal)
            .where(
                Proposal.finding_id == finding.id,
                Proposal.state.not_in([ProposalState.REJECTED, ProposalState.STALE]),
            )
            .order_by(Proposal.created_at.desc())
            .limit(1)
        )
        if existing:
            return existing
        if finding.state not in {FindingState.OPEN, FindingState.PROPOSED}:
            raise ConflictError(
                "finding_closed", "Resolved or dismissed findings cannot be proposed"
            )

        if finding.finding_type == FindingType.PROVIDER_CONFIRMED_INTERNAL_UNKNOWN:
            action = ProposalAction.CONFIRM_PAYOUT
            rationale = (
                "The provider reports a confirmed transfer for the exact idempotency "
                "key and amount; "
                "bring the internal state and ledger in line without sending another transfer."
            )
            risk = "medium"
        elif finding.finding_type == FindingType.PROVIDER_MISSING_INTERNAL_UNKNOWN:
            action = ProposalAction.MARK_FAILED_RELEASE
            rationale = (
                "The provider has no transfer for the preserved idempotency key; "
                "release the reserve "
                "and mark this attempt failed."
            )
            risk = "medium"
        else:
            action = ProposalAction.MANUAL_REVIEW
            rationale = "Evidence is ambiguous or unsafe for an automated financial correction."
            risk = "high"
        proposal = Proposal(
            finding_id=finding.id,
            action=action,
            state=ProposalState.DRAFT,
            rationale=rationale,
            risk=risk,
            evidence_hash=finding.evidence_hash,
            payout_version=finding.payout_version,
            proposed_changes={
                "payout_id": str(finding.payout_id),
                "action": action.value,
                "append_only": True,
            },
            created_at=now,
        )
        session.add(proposal)
        finding.state = FindingState.PROPOSED
        await session.flush()
    return proposal


async def _evaluate_gates(
    session: AsyncSession, proposal: Proposal, finding: Finding, payout: Payout
) -> list[dict[str, object]]:
    reserved = await _reserved_for_payout(session, payout.id)
    provider_data = finding.evidence.get("provider")
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    check(
        "evidence_hash",
        proposal.evidence_hash == finding.evidence_hash,
        "Proposal must reference the immutable finding evidence",
    )
    check(
        "payout_version",
        proposal.payout_version == payout.version == finding.payout_version,
        "Payout must not have changed since detection",
    )
    check(
        "tenant_scope",
        payout.brand_id == finding.brand_id,
        "Finding and payout must belong to the same brand",
    )
    check(
        "current_state",
        payout.status in {PayoutStatus.PENDING, PayoutStatus.UNKNOWN},
        "Only pending or unknown payouts may be reconciled",
    )
    check(
        "reserved_balance",
        reserved == payout.amount,
        "The full payout amount must still be reserved",
    )
    if proposal.action == ProposalAction.CONFIRM_PAYOUT:
        creator_id = await session.scalar(
            select(ProgramMembership.creator_id).where(ProgramMembership.id == payout.membership_id)
        )
        provider_amount: Decimal | None = None
        if isinstance(provider_data, dict) and provider_data.get("amount") is not None:
            try:
                provider_amount = Decimal(str(provider_data["amount"]))
            except Exception:
                provider_amount = None
        provider_ok = bool(
            isinstance(provider_data, dict)
            and provider_data.get("status") == "confirmed"
            and provider_amount == payout.amount
            and provider_data.get("currency") == payout.currency
            and provider_data.get("idempotency_key") == payout.idempotency_key
            and provider_data.get("payout_id") == str(payout.id)
            and provider_data.get("beneficiary_id") == str(creator_id)
        )
        check("provider_confirmation", provider_ok, "Provider evidence must match the payout")
        confirmation_exists = await session.scalar(
            select(LedgerEntry.id).where(
                LedgerEntry.payout_id == payout.id,
                LedgerEntry.idempotency_key.in_(
                    [
                        f"payout:{payout.id}:reserved-out-confirmed",
                        f"payout:{payout.id}:paid-in",
                    ]
                ),
            )
        )
        check(
            "no_duplicate_financial_effect",
            confirmation_exists is None,
            "Confirmation entries must not already exist",
        )
    elif proposal.action == ProposalAction.MARK_FAILED_RELEASE:
        check(
            "provider_absence",
            provider_data is None,
            "No provider transfer may exist when releasing the reserve",
        )
    else:
        check("executable_action", False, "Manual review proposals cannot execute")
    return checks


async def gate_proposal(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    proposal_id: uuid.UUID,
) -> tuple[Proposal, GateRun]:
    async with session.begin():
        row = (
            await session.execute(
                select(Proposal, Finding, Payout)
                .join(Finding, Finding.id == Proposal.finding_id)
                .join(Payout, Payout.id == Finding.payout_id)
                .where(Proposal.id == proposal_id, Finding.brand_id == brand_id)
                .with_for_update(of=Proposal)
            )
        ).first()
        if row is None:
            raise NotFoundError("proposal_not_found", "Proposal was not found")
        proposal = cast(Proposal, row[0])
        finding = cast(Finding, row[1])
        payout = cast(Payout, row[2])
        if proposal.state not in {ProposalState.DRAFT, ProposalState.BLOCKED}:
            raise ConflictError("proposal_not_gateable", f"Proposal is {proposal.state.value}")
        checks = await _evaluate_gates(session, proposal, finding, payout)
        passed = all(bool(item["passed"]) for item in checks)
        gate = GateRun(
            proposal_id=proposal.id,
            result=GateResult.PASSED if passed else GateResult.FAILED,
            checks=checks,
            created_at=clock.now(),
        )
        session.add(gate)
        proposal.state = ProposalState.GATED if passed else ProposalState.BLOCKED
        await session.flush()
    return proposal, gate


async def approve_proposal(
    session: AsyncSession,
    *,
    principal: Principal,
    proposal_id: uuid.UUID,
    comment: str,
) -> Proposal:
    assert principal.brand_id is not None
    async with session.begin():
        proposal = await session.scalar(
            select(Proposal)
            .join(Finding, Finding.id == Proposal.finding_id)
            .where(Proposal.id == proposal_id, Finding.brand_id == principal.brand_id)
            .with_for_update()
        )
        if proposal is None:
            raise NotFoundError("proposal_not_found", "Proposal was not found")
        if proposal.state != ProposalState.GATED:
            raise ConflictError(
                "proposal_not_approved", "Only a passing gated proposal can be approved"
            )
        proposal.state = ProposalState.APPROVED
        proposal.approved_by = principal.user_id
        proposal.approval_comment = comment
        proposal.approved_at = clock.now()
    return proposal


async def reject_proposal(
    session: AsyncSession,
    *,
    principal: Principal,
    proposal_id: uuid.UUID,
    comment: str,
) -> Proposal:
    assert principal.brand_id is not None
    async with session.begin():
        proposal = await session.scalar(
            select(Proposal)
            .join(Finding, Finding.id == Proposal.finding_id)
            .where(Proposal.id == proposal_id, Finding.brand_id == principal.brand_id)
            .with_for_update()
        )
        if proposal is None:
            raise NotFoundError("proposal_not_found", "Proposal was not found")
        if proposal.state in {ProposalState.EXECUTED, ProposalState.REJECTED}:
            raise ConflictError("proposal_not_rejectable", f"Proposal is {proposal.state.value}")
        proposal.state = ProposalState.REJECTED
        proposal.rejected_by = principal.user_id
        proposal.rejection_comment = comment
        proposal.rejected_at = clock.now()
    return proposal


async def execute_proposal(
    session: AsyncSession,
    *,
    principal: Principal,
    proposal_id: uuid.UUID,
) -> Proposal:
    assert principal.brand_id is not None
    stale = False
    async with session.begin():
        row = (
            await session.execute(
                select(Proposal, Finding, Payout)
                .join(Finding, Finding.id == Proposal.finding_id)
                .join(Payout, Payout.id == Finding.payout_id)
                .where(Proposal.id == proposal_id, Finding.brand_id == principal.brand_id)
                .with_for_update(of=(Proposal, Finding, Payout))
            )
        ).first()
        if row is None:
            raise NotFoundError("proposal_not_found", "Proposal was not found")
        proposal = cast(Proposal, row[0])
        finding = cast(Finding, row[1])
        payout = cast(Payout, row[2])
        if proposal.state == ProposalState.EXECUTED:
            return proposal
        if proposal.state != ProposalState.APPROVED or proposal.approved_by is None:
            raise ConflictError(
                "human_approval_required", "Proposal must have recorded human approval"
            )
        checks = await _evaluate_gates(session, proposal, finding, payout)
        if not all(bool(item["passed"]) for item in checks):
            proposal.state = ProposalState.STALE
            stale = True
        else:
            provider_data = finding.evidence.get("provider")
            reference = (
                str(provider_data.get("provider_reference"))
                if isinstance(provider_data, dict) and provider_data.get("provider_reference")
                else None
            )
            target = (
                PayoutStatus.CONFIRMED
                if proposal.action == ProposalAction.CONFIRM_PAYOUT
                else PayoutStatus.FAILED
            )
            now = clock.now()
            await _apply_provider_result(
                session,
                payout=payout,
                target=target,
                provider_reference=reference,
                now=now,
            )
            proposal.state = ProposalState.EXECUTED
            proposal.executed_at = now
            finding.state = FindingState.RESOLVED
            finding.resolved_at = now
            add_audit(
                session,
                brand_id=principal.brand_id,
                actor_user_id=principal.user_id,
                action="agent.proposal_executed",
                entity_type="agent_proposal",
                entity_id=proposal.id,
                data={
                    "finding_id": str(finding.id),
                    "payout_id": str(payout.id),
                    "action": proposal.action.value,
                    "approval_comment": proposal.approval_comment or "",
                },
                now=now,
            )
            enqueue_event(
                session,
                aggregate_type="payout",
                aggregate_id=payout.id,
                event_type="financial.reconciliation.applied",
                payload={
                    "payout_id": str(payout.id),
                    "proposal_id": str(proposal.id),
                    "action": proposal.action.value,
                },
                now=now,
            )
    if stale:
        raise ConflictError(
            "proposal_stale",
            "The proposal was marked stale because its evidence no longer matches current state",
        )
    return proposal
