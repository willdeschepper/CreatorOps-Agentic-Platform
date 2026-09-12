import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, require_roles
from creatorops.models.enums import BrandRole, PayoutBatchStatus, PayoutStatus
from creatorops.schemas import (
    ApprovalRequest,
    PageResponse,
    PayoutBatchCancelRequest,
    PayoutBatchCreateRequest,
    PayoutBatchDetailResponse,
    PayoutBatchResponse,
    PayoutItemResponse,
)
from creatorops.services import finance

router = APIRouter(tags=["finance"])
finance_roles = require_roles(BrandRole.OWNER, BrandRole.FINANCE)


def _batch_payload(batch: object, payouts: Sequence[object]) -> PayoutBatchDetailResponse:
    return PayoutBatchDetailResponse(
        batch=PayoutBatchResponse.model_validate(batch),
        payouts=[PayoutItemResponse.model_validate(payout) for payout in payouts],
    )


@router.post(
    "/payout-batches",
    response_model=PayoutBatchDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payout_batch(
    body: PayoutBatchCreateRequest,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> PayoutBatchDetailResponse:
    batch, payouts = await finance.create_payout_batch(
        session,
        principal,
        program_id=body.program_id,
        cutoff_at=body.cutoff_at,
        scenario=body.scenario,
    )
    return _batch_payload(batch, payouts)


@router.post("/payout-batches/{batch_id}/approve", response_model=PayoutBatchDetailResponse)
async def approve_payout_batch(
    batch_id: uuid.UUID,
    body: ApprovalRequest,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> PayoutBatchDetailResponse:
    batch, payouts = await finance.approve_payout_batch(
        session, principal, batch_id=batch_id, comment=body.comment
    )
    return _batch_payload(batch, payouts)


@router.get("/payout-batches/{batch_id}", response_model=PayoutBatchDetailResponse)
async def get_payout_batch(
    batch_id: uuid.UUID,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> PayoutBatchDetailResponse:
    assert principal.brand_id is not None
    batch, payouts = await finance.get_batch(session, principal.brand_id, batch_id)
    return _batch_payload(batch, payouts)


@router.get("/payout-batches", response_model=PageResponse[PayoutBatchResponse])
async def list_payout_batches(
    program_id: uuid.UUID | None = None,
    batch_status: PayoutBatchStatus | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[PayoutBatchResponse]:
    assert principal.brand_id is not None
    rows, total = await finance.list_batches(
        session,
        brand_id=principal.brand_id,
        program_id=program_id,
        status=batch_status,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[PayoutBatchResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/payouts", response_model=PageResponse[PayoutItemResponse])
async def list_payouts(
    program_id: uuid.UUID | None = None,
    batch_id: uuid.UUID | None = None,
    membership_id: uuid.UUID | None = None,
    payout_status: PayoutStatus | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[PayoutItemResponse]:
    assert principal.brand_id is not None
    rows, total = await finance.list_payouts(
        session,
        brand_id=principal.brand_id,
        program_id=program_id,
        batch_id=batch_id,
        membership_id=membership_id,
        status=payout_status,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[PayoutItemResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/payout-batches/{batch_id}/cancel", response_model=PayoutBatchDetailResponse)
async def cancel_payout_batch(
    batch_id: uuid.UUID,
    body: PayoutBatchCancelRequest,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> PayoutBatchDetailResponse:
    batch, payouts = await finance.cancel_payout_batch(
        session, principal=principal, batch_id=batch_id, comment=body.comment
    )
    return _batch_payload(batch, payouts)
