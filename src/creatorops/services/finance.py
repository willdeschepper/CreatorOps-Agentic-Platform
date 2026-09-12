import uuid
from datetime import datetime
from decimal import Decimal

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import session_factory
from creatorops.core.errors import ConflictError, NotFoundError, UnprocessableError
from creatorops.core.security import Principal
from creatorops.core.time import clock
from creatorops.models.commissions import LedgerEntry
from creatorops.models.enums import (
    LedgerBucket,
    LedgerEntryType,
    PayoutBatchStatus,
    PayoutStatus,
    ProviderScenario,
)
from creatorops.models.finance import Payout, PayoutBatch
from creatorops.models.partnerships import ProgramMembership
from creatorops.services.commissions import add_ledger_entry, balances_for_membership, money
from creatorops.services.programs import get_program_for_brand
from creatorops.services.provider import PayoutProvider, provider
from creatorops.services.shared import add_audit, enqueue_event


async def create_payout_batch(
    session: AsyncSession,
    principal: Principal,
    *,
    program_id: uuid.UUID,
    cutoff_at: datetime,
    scenario: ProviderScenario,
) -> tuple[PayoutBatch, list[Payout]]:
    assert principal.brand_id is not None
    now = clock.now()
    async with session.begin():
        program = await get_program_for_brand(session, program_id, principal.brand_id)
        balance_rows = (
            await session.execute(
                select(
                    LedgerEntry.membership_id,
                    func.coalesce(func.sum(LedgerEntry.amount), 0).label("available"),
                )
                .where(
                    LedgerEntry.program_id == program_id,
                    LedgerEntry.bucket == LedgerBucket.AVAILABLE,
                    LedgerEntry.created_at <= cutoff_at,
                )
                .group_by(LedgerEntry.membership_id)
                .having(func.sum(LedgerEntry.amount) >= program.payout_minimum)
                .order_by(LedgerEntry.membership_id)
            )
        ).all()
        if not balance_rows:
            raise UnprocessableError(
                "no_payouts_eligible",
                "No creator has the minimum available balance at this cutoff",
            )
        batch = PayoutBatch(
            brand_id=principal.brand_id,
            program_id=program_id,
            cutoff_at=cutoff_at,
            status=PayoutBatchStatus.DRAFT,
            created_by=principal.user_id,
        )
        session.add(batch)
        await session.flush()
        payouts: list[Payout] = []
        for membership_id, available in balance_rows:
            payout = Payout(
                batch_id=batch.id,
                brand_id=principal.brand_id,
                program_id=program_id,
                membership_id=membership_id,
                amount=money(Decimal(available)),
                currency=program.currency,
                status=PayoutStatus.DRAFT,
                idempotency_key=f"creatorops:{batch.id}:{membership_id}",
                simulation_scenario=scenario,
            )
            session.add(payout)
            payouts.append(payout)
        await session.flush()
        add_audit(
            session,
            brand_id=principal.brand_id,
            actor_user_id=principal.user_id,
            action="payout.batch_created",
            entity_type="payout_batch",
            entity_id=batch.id,
            data={"payout_count": len(payouts), "cutoff_at": cutoff_at.isoformat()},
            now=now,
        )
    return batch, payouts


async def approve_payout_batch(
    session: AsyncSession,
    principal: Principal,
    *,
    batch_id: uuid.UUID,
    comment: str,
) -> tuple[PayoutBatch, list[Payout]]:
    assert principal.brand_id is not None
    now = clock.now()
    async with session.begin():
        batch = await session.scalar(
            select(PayoutBatch)
            .where(PayoutBatch.id == batch_id, PayoutBatch.brand_id == principal.brand_id)
            .with_for_update()
        )
        if batch is None:
            raise NotFoundError("payout_batch_not_found", "Payout batch was not found")
        if batch.status != PayoutBatchStatus.DRAFT:
            if batch.status in {PayoutBatchStatus.APPROVED, PayoutBatchStatus.PROCESSING}:
                payouts = list(
                    (await session.scalars(select(Payout).where(Payout.batch_id == batch.id))).all()
                )
                return batch, payouts
            raise ConflictError(
                "payout_batch_not_approvable", f"Batch is already {batch.status.value}"
            )
        payouts = list(
            (
                await session.scalars(
                    select(Payout)
                    .where(Payout.batch_id == batch.id)
                    .order_by(Payout.id)
                    .with_for_update()
                )
            ).all()
        )
        for payout in payouts:
            await session.scalar(
                select(ProgramMembership.id)
                .where(ProgramMembership.id == payout.membership_id)
                .with_for_update()
            )
            balance = await balances_for_membership(session, payout.membership_id)
            if balance[LedgerBucket.AVAILABLE] < payout.amount:
                raise ConflictError(
                    "insufficient_creator_balance",
                    "Creator balance changed after the batch snapshot",
                    meta={
                        "membership_id": str(payout.membership_id),
                        "snapshot": str(payout.amount),
                        "current": str(balance[LedgerBucket.AVAILABLE]),
                    },
                )
            add_ledger_entry(
                session,
                brand_id=payout.brand_id,
                program_id=payout.program_id,
                membership_id=payout.membership_id,
                payout_id=payout.id,
                bucket=LedgerBucket.AVAILABLE,
                entry_type=LedgerEntryType.PAYOUT_RESERVED,
                amount=-payout.amount,
                idempotency_key=f"payout:{payout.id}:available-out",
                description="Reserve creator balance for payout",
                created_at=now,
            )
            add_ledger_entry(
                session,
                brand_id=payout.brand_id,
                program_id=payout.program_id,
                membership_id=payout.membership_id,
                payout_id=payout.id,
                bucket=LedgerBucket.RESERVED,
                entry_type=LedgerEntryType.PAYOUT_RESERVED,
                amount=payout.amount,
                idempotency_key=f"payout:{payout.id}:reserved-in",
                description="Payout amount reserved",
                created_at=now,
            )
            payout.status = PayoutStatus.PENDING
            payout.reserved_at = now
            payout.version += 1
            enqueue_event(
                session,
                aggregate_type="payout",
                aggregate_id=payout.id,
                event_type="payout.requested",
                payload={
                    "payout_id": str(payout.id),
                    "brand_id": str(payout.brand_id),
                },
                now=now,
            )
        batch.status = PayoutBatchStatus.APPROVED
        batch.approved_by = principal.user_id
        batch.approval_comment = comment
        batch.approved_at = now
        add_audit(
            session,
            brand_id=principal.brand_id,
            actor_user_id=principal.user_id,
            action="payout.batch_approved",
            entity_type="payout_batch",
            entity_id=batch.id,
            data={"comment": comment, "payout_count": len(payouts)},
            now=now,
        )
    return batch, payouts


async def _update_batch_status(session: AsyncSession, batch_id: uuid.UUID) -> None:
    batch = await session.get(PayoutBatch, batch_id)
    if batch is None:
        return
    statuses = list(
        (await session.scalars(select(Payout.status).where(Payout.batch_id == batch_id))).all()
    )
    if statuses and all(status == PayoutStatus.CONFIRMED for status in statuses):
        batch.status = PayoutBatchStatus.COMPLETED
    elif statuses and all(
        status in {PayoutStatus.CONFIRMED, PayoutStatus.FAILED} for status in statuses
    ):
        batch.status = PayoutBatchStatus.PARTIALLY_FAILED
    elif any(status != PayoutStatus.DRAFT for status in statuses):
        batch.status = PayoutBatchStatus.PROCESSING


async def _apply_provider_result(
    session: AsyncSession,
    *,
    payout: Payout,
    target: PayoutStatus,
    provider_reference: str | None,
    now: datetime,
) -> None:
    if payout.status not in {PayoutStatus.PENDING, PayoutStatus.UNKNOWN}:
        return
    if provider_reference:
        payout.provider_reference = provider_reference
    if target == PayoutStatus.CONFIRMED:
        add_ledger_entry(
            session,
            brand_id=payout.brand_id,
            program_id=payout.program_id,
            membership_id=payout.membership_id,
            payout_id=payout.id,
            bucket=LedgerBucket.RESERVED,
            entry_type=LedgerEntryType.PAYOUT_CONFIRMED,
            amount=-payout.amount,
            idempotency_key=f"payout:{payout.id}:reserved-out-confirmed",
            description="Confirmed payout leaves reserved balance",
            created_at=now,
        )
        add_ledger_entry(
            session,
            brand_id=payout.brand_id,
            program_id=payout.program_id,
            membership_id=payout.membership_id,
            payout_id=payout.id,
            bucket=LedgerBucket.PAID,
            entry_type=LedgerEntryType.PAYOUT_CONFIRMED,
            amount=payout.amount,
            idempotency_key=f"payout:{payout.id}:paid-in",
            description="Payout confirmed by provider",
            created_at=now,
        )
        payout.status = PayoutStatus.CONFIRMED
        payout.confirmed_at = now
    elif target == PayoutStatus.FAILED:
        add_ledger_entry(
            session,
            brand_id=payout.brand_id,
            program_id=payout.program_id,
            membership_id=payout.membership_id,
            payout_id=payout.id,
            bucket=LedgerBucket.RESERVED,
            entry_type=LedgerEntryType.PAYOUT_RELEASED,
            amount=-payout.amount,
            idempotency_key=f"payout:{payout.id}:reserved-out-failed",
            description="Failed payout releases reserved balance",
            created_at=now,
        )
        add_ledger_entry(
            session,
            brand_id=payout.brand_id,
            program_id=payout.program_id,
            membership_id=payout.membership_id,
            payout_id=payout.id,
            bucket=LedgerBucket.AVAILABLE,
            entry_type=LedgerEntryType.PAYOUT_RELEASED,
            amount=payout.amount,
            idempotency_key=f"payout:{payout.id}:available-returned",
            description="Failed payout returned to available balance",
            created_at=now,
        )
        payout.status = PayoutStatus.FAILED
        payout.failed_at = now
    elif target == PayoutStatus.UNKNOWN:
        payout.status = PayoutStatus.UNKNOWN
        payout.unknown_at = now
    payout.version += 1
    await _update_batch_status(session, payout.batch_id)


async def process_payout(
    payout_id: uuid.UUID, payout_provider: PayoutProvider = provider
) -> PayoutStatus | None:
    async with session_factory() as read_session:
        row = (
            await read_session.execute(
                select(Payout, ProgramMembership)
                .join(ProgramMembership, ProgramMembership.id == Payout.membership_id)
                .where(Payout.id == payout_id)
            )
        ).first()
        if row is None:
            return None
        payout_snapshot, membership = row
        if payout_snapshot.status != PayoutStatus.PENDING:
            return PayoutStatus(payout_snapshot.status)
        beneficiary_id = membership.creator_id
        amount = payout_snapshot.amount
        currency = payout_snapshot.currency
        key = payout_snapshot.idempotency_key
        scenario = payout_snapshot.simulation_scenario

    target = PayoutStatus.UNKNOWN
    reference: str | None = None
    try:
        transfer = await payout_provider.create_transfer(
            payout_id=payout_id,
            beneficiary_id=beneficiary_id,
            amount=amount,
            currency=currency,
            idempotency_key=key,
            scenario=scenario,
        )
        reference = transfer.provider_reference
        target = PayoutStatus.CONFIRMED if transfer.status == "confirmed" else PayoutStatus.FAILED
    except (httpx.TimeoutException, httpx.HTTPError):
        target = PayoutStatus.UNKNOWN

    async with session_factory() as write_session, write_session.begin():
        payout = await write_session.scalar(
            select(Payout).where(Payout.id == payout_id).with_for_update()
        )
        if payout is None:
            return None
        await _apply_provider_result(
            write_session,
            payout=payout,
            target=target,
            provider_reference=reference,
            now=clock.now(),
        )
        return payout.status


async def get_batch(
    session: AsyncSession, brand_id: uuid.UUID, batch_id: uuid.UUID
) -> tuple[PayoutBatch, list[Payout]]:
    batch = await session.scalar(
        select(PayoutBatch).where(PayoutBatch.id == batch_id, PayoutBatch.brand_id == brand_id)
    )
    if batch is None:
        raise NotFoundError("payout_batch_not_found", "Payout batch was not found")
    payouts = list((await session.scalars(select(Payout).where(Payout.batch_id == batch.id))).all())
    return batch, payouts
