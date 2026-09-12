import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.errors import NotFoundError
from creatorops.core.security import Principal
from creatorops.models.attribution import Order, OrderAttribution
from creatorops.models.commissions import Commission, LedgerEntry
from creatorops.models.enums import (
    CampaignParticipantStatus,
    CommissionKind,
    ContentStatus,
    LedgerBucket,
    MembershipStatus,
)
from creatorops.models.finance import Payout
from creatorops.models.listening import ContentEvidence
from creatorops.models.partnerships import CampaignParticipant, ProgramMembership
from creatorops.models.programs import Campaign, Program
from creatorops.schemas import (
    CampaignReportResponse,
    MembershipReportResponse,
    ReportOverviewResponse,
)
from creatorops.services.commissions import money
from creatorops.services.programs import get_program_for_brand


def _sum_metrics(rows: list[dict[str, object]]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for metrics in rows:
        for key, value in metrics.items():
            if isinstance(value, int) and not isinstance(value, bool):
                totals[key] = totals.get(key, 0) + value
    return totals


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
    metric_rows = list(
        (
            await session.scalars(
                select(ContentEvidence.metrics).where(
                    ContentEvidence.program_id == program_id,
                    ContentEvidence.brand_id == brand_id,
                    ContentEvidence.status == ContentStatus.APPROVED,
                )
            )
        ).all()
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
        social_metrics=_sum_metrics(metric_rows),
    )


async def campaign_overview(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    campaign_id: uuid.UUID,
) -> CampaignReportResponse:
    campaign = await session.scalar(
        select(Campaign)
        .join(Program, Program.id == Campaign.program_id)
        .where(Campaign.id == campaign_id, Program.brand_id == brand_id)
    )
    if campaign is None:
        raise NotFoundError("campaign_not_found", "Campaign was not found")
    order_row = (
        await session.execute(
            select(
                func.coalesce(func.sum(Order.gross_amount), 0),
                func.coalesce(func.sum(Order.refunded_amount), 0),
                func.count(Order.id),
            )
            .join(OrderAttribution, OrderAttribution.order_id == Order.id)
            .where(
                Order.brand_id == brand_id,
                OrderAttribution.campaign_id == campaign_id,
            )
        )
    ).one()
    selected = await session.scalar(
        select(func.count(CampaignParticipant.id)).where(
            CampaignParticipant.campaign_id == campaign_id,
            CampaignParticipant.status == CampaignParticipantStatus.SELECTED,
        )
    )
    post_rows = list(
        (
            await session.scalars(
                select(ContentEvidence.metrics).where(
                    ContentEvidence.brand_id == brand_id,
                    ContentEvidence.campaign_id == campaign_id,
                    ContentEvidence.status == ContentStatus.APPROVED,
                )
            )
        ).all()
    )
    commission_row = (
        await session.execute(
            select(
                func.coalesce(
                    func.sum(Commission.amount).filter(
                        Commission.kind != CommissionKind.REFUND_ADJUSTMENT
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(Commission.amount).filter(
                        Commission.kind == CommissionKind.REFUND_ADJUSTMENT
                    ),
                    0,
                ),
            )
            .join(OrderAttribution, OrderAttribution.order_id == Commission.order_id)
            .join(Order, Order.id == Commission.order_id)
            .where(
                Order.brand_id == brand_id,
                OrderAttribution.campaign_id == campaign_id,
            )
        )
    ).one()
    gross = money(Decimal(order_row[0]))
    refunded = money(Decimal(order_row[1]))
    accrued = money(Decimal(commission_row[0]))
    adjustments = money(Decimal(commission_row[1]))
    return CampaignReportResponse(
        campaign_id=campaign.id,
        program_id=campaign.program_id,
        gmv=gross,
        refunded_gmv=refunded,
        net_gmv=money(gross - refunded),
        orders=int(order_row[2]),
        selected_creators=int(selected or 0),
        approved_posts=len(post_rows),
        social_metrics=_sum_metrics(post_rows),
        commission_accrued=accrued,
        commission_adjustments=adjustments,
        net_commission=money(accrued + adjustments),
    )


async def membership_overview(
    session: AsyncSession,
    *,
    principal: Principal,
    membership_id: uuid.UUID,
) -> MembershipReportResponse:
    statement = (
        select(ProgramMembership, Program)
        .join(Program, Program.id == ProgramMembership.program_id)
        .where(ProgramMembership.id == membership_id)
    )
    if principal.brand_id is None:
        statement = statement.where(ProgramMembership.creator_id == principal.user_id)
    else:
        statement = statement.where(Program.brand_id == principal.brand_id)
    row = (await session.execute(statement)).first()
    if row is None:
        raise NotFoundError("membership_not_found", "Membership was not found")
    membership, program = row
    order_row = (
        await session.execute(
            select(
                func.coalesce(func.sum(Order.gross_amount), 0),
                func.coalesce(func.sum(Order.refunded_amount), 0),
                func.count(Order.id),
            )
            .join(OrderAttribution, OrderAttribution.order_id == Order.id)
            .where(
                Order.brand_id == program.brand_id,
                OrderAttribution.membership_id == membership.id,
            )
        )
    ).one()
    post_rows = list(
        (
            await session.scalars(
                select(ContentEvidence.metrics).where(
                    ContentEvidence.brand_id == program.brand_id,
                    ContentEvidence.membership_id == membership.id,
                    ContentEvidence.status == ContentStatus.APPROVED,
                )
            )
        ).all()
    )
    ledger_rows = (
        await session.execute(
            select(LedgerEntry.bucket, func.coalesce(func.sum(LedgerEntry.amount), 0))
            .where(
                LedgerEntry.brand_id == program.brand_id,
                LedgerEntry.membership_id == membership.id,
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
            .where(
                Payout.brand_id == program.brand_id,
                Payout.membership_id == membership.id,
            )
            .group_by(Payout.status)
        )
    ).all()
    gross = money(Decimal(order_row[0]))
    refunded = money(Decimal(order_row[1]))
    return MembershipReportResponse(
        membership_id=membership.id,
        program_id=membership.program_id,
        gmv=gross,
        refunded_gmv=refunded,
        net_gmv=money(gross - refunded),
        orders=int(order_row[2]),
        approved_posts=len(post_rows),
        social_metrics=_sum_metrics(post_rows),
        commission_pending=balances[LedgerBucket.PENDING],
        commission_available=balances[LedgerBucket.AVAILABLE],
        commission_reserved=balances[LedgerBucket.RESERVED],
        commission_paid=balances[LedgerBucket.PAID],
        payouts={status.value: int(count) for status, count in payout_rows},
    )
