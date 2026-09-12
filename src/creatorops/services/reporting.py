import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.models.attribution import Order, OrderAttribution
from creatorops.models.commissions import LedgerEntry
from creatorops.models.enums import ContentStatus, LedgerBucket, MembershipStatus
from creatorops.models.finance import Payout
from creatorops.models.listening import ContentEvidence
from creatorops.models.partnerships import ProgramMembership
from creatorops.schemas import ReportOverviewResponse
from creatorops.services.commissions import money
from creatorops.services.programs import get_program_for_brand


async def program_overview(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    program_id: uuid.UUID,
) -> ReportOverviewResponse:
    await get_program_for_brand(session, program_id, brand_id)
    order_row = (
        await session.execute(
            select(
                func.coalesce(func.sum(Order.gross_amount), 0),
                func.coalesce(func.sum(Order.refunded_amount), 0),
                func.count(Order.id),
                func.count(OrderAttribution.id).filter(OrderAttribution.membership_id.is_not(None)),
            )
            .outerjoin(OrderAttribution, OrderAttribution.order_id == Order.id)
            .where(Order.program_id == program_id, Order.brand_id == brand_id)
        )
    ).one()
    creators = await session.scalar(
        select(func.count(ProgramMembership.id)).where(
            ProgramMembership.program_id == program_id,
            ProgramMembership.status == MembershipStatus.ACTIVE,
        )
    )
    posts = await session.scalar(
        select(func.count(ContentEvidence.id)).where(
            ContentEvidence.program_id == program_id,
            ContentEvidence.brand_id == brand_id,
            ContentEvidence.status == ContentStatus.APPROVED,
        )
    )
    ledger_rows = (
        await session.execute(
            select(LedgerEntry.bucket, func.coalesce(func.sum(LedgerEntry.amount), 0))
            .where(
                LedgerEntry.program_id == program_id,
                LedgerEntry.brand_id == brand_id,
            )
            .group_by(LedgerEntry.bucket)
        )
    ).all()
    balances = {bucket: Decimal("0.00") for bucket in LedgerBucket}
    for bucket, amount in ledger_rows:
        balances[bucket] = money(Decimal(amount))
    payout_rows = (
        await session.execute(
            select(Payout.status, func.count(Payout.id))
            .where(Payout.program_id == program_id, Payout.brand_id == brand_id)
            .group_by(Payout.status)
        )
    ).all()
    gross = money(Decimal(order_row[0]))
    refunded = money(Decimal(order_row[1]))
    return ReportOverviewResponse(
        program_id=program_id,
        gmv=gross,
        refunded_gmv=refunded,
        net_gmv=money(gross - refunded),
        orders=int(order_row[2]),
        attributed_orders=int(order_row[3]),
        active_creators=int(creators or 0),
        approved_posts=int(posts or 0),
        commission_pending=balances[LedgerBucket.PENDING],
        commission_available=balances[LedgerBucket.AVAILABLE],
        commission_reserved=balances[LedgerBucket.RESERVED],
        commission_paid=balances[LedgerBucket.PAID],
        payouts={status.value: int(count) for status, count in payout_rows},
    )
