import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, get_principal, require_roles
from creatorops.models.enums import (
    BrandRole,
    CommissionKind,
    CommissionStatus,
    LedgerBucket,
    OrderStatus,
)
from creatorops.schemas import (
    AuditLogResponse,
    CommissionResponse,
    LedgerEntryResponse,
    OrderAttributionResponse,
    OrderDetailResponse,
    OrderResponse,
    PageResponse,
)
from creatorops.services import operations

router = APIRouter(tags=["operations"])
staff_roles = require_roles(BrandRole.OWNER, BrandRole.OPS, BrandRole.FINANCE)
finance_roles = require_roles(BrandRole.OWNER, BrandRole.FINANCE)


@router.get("/orders", response_model=PageResponse[OrderResponse])
async def list_orders(
    program_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    membership_id: uuid.UUID | None = None,
    order_status: OrderStatus | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(staff_roles),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[OrderResponse]:
    assert principal.brand_id is not None
    rows, total = await operations.list_orders(
        session,
        brand_id=principal.brand_id,
        program_id=program_id,
        campaign_id=campaign_id,
        membership_id=membership_id,
        status=order_status,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[OrderResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/orders/{order_id}", response_model=OrderDetailResponse)
async def get_order(
    order_id: uuid.UUID,
    principal: Principal = Depends(staff_roles),
    session: AsyncSession = Depends(get_session),
) -> OrderDetailResponse:
    assert principal.brand_id is not None
    order, attribution, commissions = await operations.get_order_detail(
        session, brand_id=principal.brand_id, order_id=order_id
    )
    return OrderDetailResponse(
        **OrderResponse.model_validate(order).model_dump(),
        attribution=(OrderAttributionResponse.model_validate(attribution) if attribution else None),
        commissions=[CommissionResponse.model_validate(row) for row in commissions],
    )


@router.get("/commissions", response_model=PageResponse[CommissionResponse])
async def list_commissions(
    program_id: uuid.UUID | None = None,
    membership_id: uuid.UUID | None = None,
    commission_status: CommissionStatus | None = None,
    commission_kind: CommissionKind | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[CommissionResponse]:
    assert principal.brand_id is not None
    rows, total = await operations.list_commissions(
        session,
        brand_id=principal.brand_id,
        program_id=program_id,
        membership_id=membership_id,
        status=commission_status,
        kind=commission_kind,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[CommissionResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/memberships/{membership_id}/commissions",
    response_model=PageResponse[CommissionResponse],
)
async def membership_commissions(
    membership_id: uuid.UUID,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[CommissionResponse]:
    rows, total = await operations.list_creator_commissions(
        session,
        principal=principal,
        membership_id=membership_id,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[CommissionResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/ledger-entries", response_model=PageResponse[LedgerEntryResponse])
async def list_ledger_entries(
    program_id: uuid.UUID | None = None,
    membership_id: uuid.UUID | None = None,
    bucket: LedgerBucket | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[LedgerEntryResponse]:
    assert principal.brand_id is not None
    rows, total = await operations.list_ledger_entries(
        session,
        brand_id=principal.brand_id,
        program_id=program_id,
        membership_id=membership_id,
        bucket=bucket,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[LedgerEntryResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/audit-logs", response_model=PageResponse[AuditLogResponse])
async def list_audit_logs(
    actor_user_id: uuid.UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    from_at: datetime | None = None,
    to_at: datetime | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(staff_roles),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[AuditLogResponse]:
    assert principal.brand_id is not None
    rows, total = await operations.list_audit_logs(
        session,
        brand_id=principal.brand_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        from_at=from_at,
        to_at=to_at,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[AuditLogResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
