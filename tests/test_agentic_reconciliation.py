import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import func, select

from creatorops.core.db import session_factory
from creatorops.core.errors import ConflictError
from creatorops.core.security import Principal
from creatorops.models.agent_control import Finding, Proposal
from creatorops.models.commissions import LedgerEntry
from creatorops.models.enums import (
    BrandRole,
    FindingState,
    FindingType,
    GateResult,
    LedgerBucket,
    LedgerEntryType,
    PayoutStatus,
    ProposalState,
    ProviderScenario,
    UserKind,
)
from creatorops.models.finance import Payout
from creatorops.services import agent_control, finance
from creatorops.services.commissions import add_ledger_entry, balances_for_membership
from creatorops.services.provider import ProviderTransfer
from tests.helpers import DomainFixture, create_domain_fixture, unique


class TimeoutAfterProvider:
    def __init__(self) -> None:
        self.transfer: ProviderTransfer | None = None
        self.create_calls = 0

    async def create_transfer(
        self,
        *,
        payout_id: uuid.UUID,
        beneficiary_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        scenario: ProviderScenario,
    ) -> ProviderTransfer:
        self.create_calls += 1
        self.transfer = ProviderTransfer(
            provider_reference=unique("tr"),
            idempotency_key=idempotency_key,
            payout_id=payout_id,
            beneficiary_id=beneficiary_id,
            amount=amount,
            currency=currency,
            status="confirmed",
        )
        raise httpx.ReadTimeout("simulated timeout after provider commit")

    async def find_by_key(self, idempotency_key: str) -> ProviderTransfer | None:
        if self.transfer and self.transfer.idempotency_key == idempotency_key:
            return self.transfer
        return None

    async def statement(self, payout_id: uuid.UUID) -> list[ProviderTransfer]:
        if self.transfer and self.transfer.payout_id == payout_id:
            return [self.transfer]
        return []


async def _unknown_payout() -> tuple[DomainFixture, Principal, Payout, TimeoutAfterProvider]:
    fixture = await create_domain_fixture(role=BrandRole.FINANCE, creator_count=1)
    creator = fixture.creators[0]
    principal = Principal(
        user_id=fixture.staff_user_id,
        kind=UserKind.STAFF,
        brand_id=fixture.brand_id,
        role=BrandRole.FINANCE,
    )
    now = datetime.now(UTC)
    async with session_factory() as session, session.begin():
        add_ledger_entry(
            session,
            brand_id=fixture.brand_id,
            program_id=fixture.program_id,
            membership_id=creator.membership_id,
            bucket=LedgerBucket.AVAILABLE,
            entry_type=LedgerEntryType.RECONCILIATION_ADJUSTMENT,
            amount=Decimal("50.00"),
            idempotency_key=unique("fund-balance"),
            description="Test funding entry",
            created_at=now,
        )
    async with session_factory() as session:
        batch, _payouts = await finance.create_payout_batch(
            session,
            principal,
            program_id=fixture.program_id,
            cutoff_at=now + timedelta(minutes=1),
            scenario=ProviderScenario.TIMEOUT_AFTER,
        )
    async with session_factory() as session:
        _batch, approved = await finance.approve_payout_batch(
            session,
            principal,
            batch_id=batch.id,
            comment="Financial test approval",
        )
    payout = approved[0]
    provider = TimeoutAfterProvider()
    assert await finance.process_payout(payout.id, provider) == PayoutStatus.UNKNOWN
    return fixture, principal, payout, provider


async def test_unknown_payout_requires_gates_human_approval_and_no_retry() -> None:
    fixture, principal, payout, provider = await _unknown_payout()
    assert principal.brand_id is not None
    run, findings = await agent_control.run_reconciliation(
        brand_id=principal.brand_id,
        started_by=principal.user_id,
        payout_provider=provider,
    )
    assert run.summary["new_findings"] == 1
    finding = findings[0]
    assert finding.finding_type == FindingType.PROVIDER_CONFIRMED_INTERNAL_UNKNOWN

    async with session_factory() as session:
        proposal = await agent_control.generate_proposal(
            session, brand_id=principal.brand_id, finding_id=finding.id
        )
    async with session_factory() as session:
        proposal, gate = await agent_control.gate_proposal(
            session, brand_id=principal.brand_id, proposal_id=proposal.id
        )
    assert gate.result == GateResult.PASSED
    assert all(check["passed"] for check in gate.checks)

    with pytest.raises(ConflictError, match="human approval"):
        async with session_factory() as session:
            await agent_control.execute_proposal(
                session, principal=principal, proposal_id=proposal.id
            )
    async with session_factory() as session:
        await agent_control.approve_proposal(
            session,
            principal=principal,
            proposal_id=proposal.id,
            comment="Provider evidence manually checked",
        )
    async with session_factory() as session:
        executed = await agent_control.execute_proposal(
            session, principal=principal, proposal_id=proposal.id
        )
    assert executed.state == ProposalState.EXECUTED
    assert provider.create_calls == 1

    async with session_factory() as session:
        persisted_payout = await session.get(Payout, payout.id)
        persisted_finding = await session.get(Finding, finding.id)
        balance = await balances_for_membership(session, fixture.creators[0].membership_id)
        financial_entries = await session.scalar(
            select(func.count(LedgerEntry.id)).where(LedgerEntry.payout_id == payout.id)
        )
    assert persisted_payout is not None
    assert persisted_payout.status == PayoutStatus.CONFIRMED
    assert persisted_finding is not None
    assert persisted_finding.state == FindingState.RESOLVED
    assert balance[LedgerBucket.RESERVED] == Decimal("0.00")
    assert balance[LedgerBucket.PAID] == Decimal("50.00")
    assert financial_entries == 4


async def test_executor_marks_approved_proposal_stale_when_payout_changes() -> None:
    _fixture, principal, payout, provider = await _unknown_payout()
    assert principal.brand_id is not None
    _run, findings = await agent_control.run_reconciliation(
        brand_id=principal.brand_id,
        started_by=principal.user_id,
        payout_provider=provider,
    )
    finding = findings[0]
    async with session_factory() as session:
        proposal = await agent_control.generate_proposal(
            session, brand_id=principal.brand_id, finding_id=finding.id
        )
    async with session_factory() as session:
        proposal, _gate = await agent_control.gate_proposal(
            session, brand_id=principal.brand_id, proposal_id=proposal.id
        )
    async with session_factory() as session:
        await agent_control.approve_proposal(
            session,
            principal=principal,
            proposal_id=proposal.id,
            comment="Evidence looked correct at approval time",
        )
    async with session_factory() as session, session.begin():
        changed = await session.get(Payout, payout.id, with_for_update=True)
        assert changed is not None
        changed.version += 1

    with pytest.raises(ConflictError, match="marked stale"):
        async with session_factory() as session:
            await agent_control.execute_proposal(
                session, principal=principal, proposal_id=proposal.id
            )
    async with session_factory() as session:
        persisted = await session.get(Proposal, proposal.id)
    assert persisted is not None
    assert persisted.state == ProposalState.STALE
