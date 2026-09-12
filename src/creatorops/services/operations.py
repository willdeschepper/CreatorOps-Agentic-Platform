import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.errors import NotFoundError
from creatorops.core.security import Principal
from creatorops.models.attribution import Order, OrderAttribution
from creatorops.models.commissions import Commission, LedgerEntry
from creatorops.models.enums import (
    CommissionKind,
    CommissionStatus,
    LedgerBucket,
    OrderStatus,
)
from creatorops.models.events import AuditLog
from creatorops.models.partnerships import ProgramMembership
from creatorops.models.programs import Program


async def list_orders(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    program_id: uuid.UUID | None,
    campaign_id: uuid.UUID | None,
    membership_id: uuid.UUID | None,
    status: OrderStatus | None,
    limit: int,
    offset: int,
) -> tuple[list[Order], int]:
    filters = [Order.brand_id == brand_id]
    if program_id:
        filters.append(Order.program_id == program_id)
    if status:
        filters.append(Order.status == status)
    statement = select(Order)
    count_statement = select(func.count(Order.id))
    if campaign_id or membership_id:
        statement = statement.join(OrderAttribution, OrderAttribution.order_id == Order.id)
        count_statement = count_statement.join(
            OrderAttribution, OrderAttribution.order_id == Order.id
        )
        if campaign_id:
            filters.append(OrderAttribution.campaign_id == campaign_id)
        if membership_id:
            filters.append(OrderAttribution.membership_id == membership_id)
    total = int(await session.scalar(count_statement.where(*filters)) or 0)
    rows = list(
        (
            await session.scalars(
                statement.where(*filters)
                .order_by(Order.created_at.desc(), Order.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def get_order_detail(
    session: AsyncSession, *, brand_id: uuid.UUID, order_id: uuid.UUID
) -> tuple[Order, OrderAttribution | None, list[Commission]]:
    order = await session.scalar(
        select(Order).where(Order.id == order_id, Order.brand_id == brand_id)
    )
    if order is None:
        raise NotFoundError("order_not_found", "Order was not found")
    attribution = await session.scalar(
        select(OrderAttribution).where(OrderAttribution.order_id == order.id)
    )
    commissions = list(
        (
            await session.scalars(
                select(Commission)
                .where(Commission.order_id == order.id)
                .order_by(Commission.created_at, Commission.id)
            )
        ).all()
    )
    return order, attribution, commissions


async def list_commissions(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    program_id: uuid.UUID | None,
    membership_id: uuid.UUID | None,
    status: CommissionStatus | None,
    kind: CommissionKind | None,
    limit: int,
    offset: int,
) -> tuple[list[Commission], int]:
    filters = [Program.brand_id == brand_id]
    if program_id:
        filters.append(Program.id == program_id)
    if membership_id:
        filters.append(Commission.membership_id == membership_id)
    if status:
        filters.append(Commission.status == status)
    if kind:
        filters.append(Commission.kind == kind)
    base = (
        select(Commission)
        .join(ProgramMembership, ProgramMembership.id == Commission.membership_id)
        .join(Program, Program.id == ProgramMembership.program_id)
    )
    count = (
        select(func.count(Commission.id))
        .join(ProgramMembership, ProgramMembership.id == Commission.membership_id)
        .join(Program, Program.id == ProgramMembership.program_id)
    )
    total = int(await session.scalar(count.where(*filters)) or 0)
    rows = list(
        (
            await session.scalars(
                base.where(*filters)
                .order_by(Commission.created_at.desc(), Commission.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def list_creator_commissions(
    session: AsyncSession,
    *,
    principal: Principal,
    membership_id: uuid.UUID,
    limit: int,
    offset: int,
) -> tuple[list[Commission], int]:
    statement = select(ProgramMembership.id).where(ProgramMembership.id == membership_id)
    if principal.brand_id is None:
        statement = statement.where(ProgramMembership.creator_id == principal.user_id)
    else:
        statement = statement.join(Program, Program.id == ProgramMembership.program_id).where(
            Program.brand_id == principal.brand_id
        )
    if await session.scalar(statement) is None:
        raise NotFoundError("membership_not_found", "Membership was not found")
    filters = [Commission.membership_id == membership_id]
    total = int(
        await session.scalar(select(func.count()).select_from(Commission).where(*filters)) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(Commission)
                .where(*filters)
                .order_by(Commission.created_at.desc(), Commission.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def list_ledger_entries(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    program_id: uuid.UUID | None,
    membership_id: uuid.UUID | None,
    bucket: LedgerBucket | None,
    limit: int,
    offset: int,
) -> tuple[list[LedgerEntry], int]:
    filters = [LedgerEntry.brand_id == brand_id]
    if program_id:
        filters.append(LedgerEntry.program_id == program_id)
    if membership_id:
        filters.append(LedgerEntry.membership_id == membership_id)
    if bucket:
        filters.append(LedgerEntry.bucket == bucket)
    total = int(
        await session.scalar(select(func.count()).select_from(LedgerEntry).where(*filters)) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(LedgerEntry)
                .where(*filters)
                .order_by(LedgerEntry.created_at.desc(), LedgerEntry.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def list_audit_logs(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    action: str | None,
    entity_type: str | None,
    from_at: datetime | None,
    to_at: datetime | None,
    limit: int,
    offset: int,
) -> tuple[list[AuditLog], int]:
    filters = [AuditLog.brand_id == brand_id]
    if actor_user_id:
        filters.append(AuditLog.actor_user_id == actor_user_id)
    if action:
        filters.append(AuditLog.action == action)
    if entity_type:
        filters.append(AuditLog.entity_type == entity_type)
    if from_at:
        filters.append(AuditLog.created_at >= from_at)
    if to_at:
        filters.append(AuditLog.created_at <= to_at)
    total = int(
        await session.scalar(select(func.count()).select_from(AuditLog).where(*filters)) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(AuditLog)
                .where(*filters)
                .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total
