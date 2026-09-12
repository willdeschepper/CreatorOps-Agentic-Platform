import uuid
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.time import clock
from creatorops.models.attribution import Order, OrderAttribution
from creatorops.models.commissions import (
    BonusRule,
    Commission,
    CommissionPlan,
    CommissionTier,
    LedgerEntry,
)
from creatorops.models.enums import (
    CommissionKind,
    CommissionMetric,
    CommissionStatus,
    LedgerBucket,
    LedgerEntryType,
    OrderStatus,
)
from creatorops.models.programs import Program

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def period_key(occurred_at: datetime) -> str:
    normalized = occurred_at.astimezone(UTC)
    return f"{normalized.year:04d}-{normalized.month:02d}"


async def select_plan(
    session: AsyncSession,
    *,
    program_id: uuid.UUID,
    campaign_id: uuid.UUID | None,
    occurred_at: datetime,
) -> CommissionPlan | None:
    if campaign_id:
        campaign_plan = await session.scalar(
            select(CommissionPlan)
            .where(
                CommissionPlan.program_id == program_id,
                CommissionPlan.campaign_id == campaign_id,
                CommissionPlan.active_from <= occurred_at,
            )
            .order_by(CommissionPlan.active_from.desc(), CommissionPlan.version.desc())
            .limit(1)
        )
        if campaign_plan:
            return campaign_plan
    return cast(
        CommissionPlan | None,
        await session.scalar(
            select(CommissionPlan)
            .where(
                CommissionPlan.program_id == program_id,
                CommissionPlan.campaign_id.is_(None),
                CommissionPlan.active_from <= occurred_at,
            )
            .order_by(CommissionPlan.active_from.desc(), CommissionPlan.version.desc())
            .limit(1)
        ),
    )


async def _month_performance(
    session: AsyncSession,
    *,
    membership_id: uuid.UUID,
    occurred_at: datetime,
) -> tuple[Decimal, int]:
    normalized = occurred_at.astimezone(UTC)
    start = datetime(normalized.year, normalized.month, 1, tzinfo=UTC)
    if normalized.month == 12:
        end = datetime(normalized.year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(normalized.year, normalized.month + 1, 1, tzinfo=UTC)
    row = (
        await session.execute(
            select(
                func.coalesce(func.sum(Order.gross_amount - Order.refunded_amount), 0),
                func.count(Order.id),
            )
            .join(OrderAttribution, OrderAttribution.order_id == Order.id)
            .where(
                OrderAttribution.membership_id == membership_id,
                Order.paid_at >= start,
                Order.paid_at < end,
                Order.status.in_(
                    [OrderStatus.PAID, OrderStatus.PARTIALLY_REFUNDED, OrderStatus.REFUNDED]
                ),
            )
        )
    ).one()
    return Decimal(row[0]), int(row[1])


def add_ledger_entry(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    program_id: uuid.UUID,
    membership_id: uuid.UUID,
    bucket: LedgerBucket,
    entry_type: LedgerEntryType,
    amount: Decimal,
    idempotency_key: str,
    description: str,
    commission_id: uuid.UUID | None = None,
    payout_id: uuid.UUID | None = None,
    currency: str = "BRL",
    created_at: datetime | None = None,
) -> LedgerEntry:
    entry = LedgerEntry(
        brand_id=brand_id,
        program_id=program_id,
        membership_id=membership_id,
        commission_id=commission_id,
        payout_id=payout_id,
        bucket=bucket,
        entry_type=entry_type,
        amount=money(amount),
        currency=currency,
        idempotency_key=idempotency_key,
        description=description,
        created_at=created_at or clock.now(),
    )
    session.add(entry)
    return entry


async def accrue_order_commissions(
    session: AsyncSession,
    *,
    order: Order,
    attribution: OrderAttribution,
    source_event_id: uuid.UUID,
    occurred_at: datetime,
) -> list[Commission]:
    if attribution.membership_id is None or order.program_id is None:
        return []
    plan = await select_plan(
        session,
        program_id=order.program_id,
        campaign_id=attribution.campaign_id,
        occurred_at=occurred_at,
    )
    if plan is None:
        return []
    await session.flush()
    cumulative_gmv, order_count = await _month_performance(
        session,
        membership_id=attribution.membership_id,
        occurred_at=occurred_at,
    )
    tiers = list(
        (
            await session.scalars(
                select(CommissionTier)
                .where(CommissionTier.plan_id == plan.id)
                .order_by(CommissionTier.threshold_gmv)
            )
        ).all()
    )
    rate = plan.base_rate
    for tier in tiers:
        if cumulative_gmv >= tier.threshold_gmv:
            rate = tier.rate

    program = await session.get(Program, order.program_id)
    if program is None:
        return []
    key = period_key(occurred_at)
    eligible_at = occurred_at + timedelta(days=plan.return_window_days)
    sale = Commission(
        order_id=order.id,
        membership_id=attribution.membership_id,
        plan_id=plan.id,
        plan_version=plan.version,
        source_event_id=source_event_id,
        kind=CommissionKind.SALE,
        status=CommissionStatus.PENDING,
        gross_basis=order.gross_amount,
        rate=rate,
        amount=money(order.gross_amount * rate),
        period_key=key,
        eligible_at=eligible_at,
    )
    session.add(sale)
    await session.flush()
    add_ledger_entry(
        session,
        brand_id=order.brand_id,
        program_id=order.program_id,
        membership_id=attribution.membership_id,
        commission_id=sale.id,
        bucket=LedgerBucket.PENDING,
        entry_type=LedgerEntryType.COMMISSION_ACCRUED,
        amount=sale.amount,
        idempotency_key=f"commission:{sale.id}:pending",
        description=f"Commission accrued for order {order.external_id}",
        created_at=occurred_at,
    )
    created = [sale]

    bonus_rules = list(
        (await session.scalars(select(BonusRule).where(BonusRule.plan_id == plan.id))).all()
    )
    for rule in bonus_rules:
        performance = (
            cumulative_gmv if rule.metric == CommissionMetric.GMV else Decimal(order_count)
        )
        if performance < rule.threshold:
            continue
        existing_bonus = await session.scalar(
            select(Commission.id).where(
                Commission.membership_id == attribution.membership_id,
                Commission.bonus_rule_id == rule.id,
                Commission.period_key == key,
            )
        )
        if existing_bonus:
            continue
        bonus = Commission(
            order_id=order.id,
            membership_id=attribution.membership_id,
            plan_id=plan.id,
            plan_version=plan.version,
            bonus_rule_id=rule.id,
            source_event_id=source_event_id,
            kind=CommissionKind.BONUS,
            status=CommissionStatus.PENDING,
            gross_basis=performance,
            rate=Decimal("0"),
            amount=money(rule.amount),
            period_key=key,
            eligible_at=eligible_at,
        )
        session.add(bonus)
        await session.flush()
        add_ledger_entry(
            session,
            brand_id=order.brand_id,
            program_id=order.program_id,
            membership_id=attribution.membership_id,
            commission_id=bonus.id,
            bucket=LedgerBucket.PENDING,
            entry_type=LedgerEntryType.COMMISSION_ACCRUED,
            amount=bonus.amount,
            idempotency_key=f"commission:{bonus.id}:pending",
            description=f"Bonus '{rule.name}' reached in {key}",
            created_at=occurred_at,
        )
        created.append(bonus)
    return created


async def create_refund_adjustments(
    session: AsyncSession,
    *,
    order: Order,
    source_event_id: uuid.UUID,
    refund_delta: Decimal,
    occurred_at: datetime,
) -> list[Commission]:
    if order.program_id is None or order.gross_amount <= 0 or refund_delta <= 0:
        return []
    originals = list(
        (
            await session.scalars(
                select(Commission).where(
                    Commission.order_id == order.id,
                    Commission.kind.in_([CommissionKind.SALE, CommissionKind.BONUS]),
                )
            )
        ).all()
    )
    adjustments: list[Commission] = []
    for original in originals:
        if original.kind == CommissionKind.BONUS and order.refunded_amount < order.gross_amount:
            continue
        factor = (
            Decimal("1")
            if original.kind == CommissionKind.BONUS
            else refund_delta / order.gross_amount
        )
        amount = money(-(original.amount * factor))
        bucket = (
            LedgerBucket.PENDING
            if original.status == CommissionStatus.PENDING
            else LedgerBucket.AVAILABLE
        )
        adjustment = Commission(
            order_id=order.id,
            membership_id=original.membership_id,
            plan_id=original.plan_id,
            plan_version=original.plan_version,
            adjustment_of_id=original.id,
            source_event_id=source_event_id,
            kind=CommissionKind.REFUND_ADJUSTMENT,
            status=(
                CommissionStatus.PENDING
                if bucket == LedgerBucket.PENDING
                else CommissionStatus.AVAILABLE
            ),
            gross_basis=refund_delta,
            rate=original.rate,
            amount=amount,
            period_key=original.period_key,
            eligible_at=occurred_at,
            available_at=occurred_at if bucket == LedgerBucket.AVAILABLE else None,
        )
        session.add(adjustment)
        await session.flush()
        add_ledger_entry(
            session,
            brand_id=order.brand_id,
            program_id=order.program_id,
            membership_id=original.membership_id,
            commission_id=adjustment.id,
            bucket=bucket,
            entry_type=LedgerEntryType.COMMISSION_REVERSED,
            amount=amount,
            idempotency_key=f"refund:{source_event_id}:{original.id}",
            description=f"Refund adjustment for order {order.external_id}",
            created_at=occurred_at,
        )
        adjustments.append(adjustment)
    return adjustments


async def settle_due_commissions(
    session: AsyncSession, *, as_of: datetime | None = None, limit: int = 500
) -> int:
    effective_at = as_of or clock.now()
    settled = 0
    async with session.begin():
        rows = list(
            (
                await session.scalars(
                    select(Commission)
                    .where(
                        Commission.status == CommissionStatus.PENDING,
                        Commission.eligible_at <= effective_at,
                    )
                    .order_by(Commission.eligible_at)
                    .limit(limit)
                    .with_for_update(skip_locked=True)
                )
            ).all()
        )
        for commission in rows:
            order = await session.get(Order, commission.order_id)
            if order is None or order.program_id is None:
                continue
            add_ledger_entry(
                session,
                brand_id=order.brand_id,
                program_id=order.program_id,
                membership_id=commission.membership_id,
                commission_id=commission.id,
                bucket=LedgerBucket.PENDING,
                entry_type=LedgerEntryType.COMMISSION_SETTLED,
                amount=-commission.amount,
                idempotency_key=f"commission:{commission.id}:pending-out",
                description="Move commission out of pending balance",
                created_at=effective_at,
            )
            add_ledger_entry(
                session,
                brand_id=order.brand_id,
                program_id=order.program_id,
                membership_id=commission.membership_id,
                commission_id=commission.id,
                bucket=LedgerBucket.AVAILABLE,
                entry_type=LedgerEntryType.COMMISSION_SETTLED,
                amount=commission.amount,
                idempotency_key=f"commission:{commission.id}:available-in",
                description="Commission became available",
                created_at=effective_at,
            )
            commission.status = CommissionStatus.AVAILABLE
            commission.available_at = effective_at
            settled += 1
    return settled


async def balances_for_membership(
    session: AsyncSession, membership_id: uuid.UUID
) -> dict[LedgerBucket, Decimal]:
    rows = (
        await session.execute(
            select(LedgerEntry.bucket, func.coalesce(func.sum(LedgerEntry.amount), 0))
            .where(LedgerEntry.membership_id == membership_id)
            .group_by(LedgerEntry.bucket)
        )
    ).all()
    result = {bucket: Decimal("0.00") for bucket in LedgerBucket}
    for bucket, amount in rows:
        result[bucket] = money(Decimal(amount))
    return result
