import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, require_roles
from creatorops.models.enums import BrandRole
from creatorops.schemas import (
    ApprovalRequest,
    PayoutBatchCreateRequest,
    PayoutBatchResponse,
    PayoutItemResponse,
)
from creatorops.services import finance

router = APIRouter(tags=["finance"])
finance_roles = require_roles(BrandRole.OWNER, BrandRole.FINANCE)


def _batch_payload(batch: object, payouts: Sequence[object]) -> dict[str, object]:
    return {
        "batch": PayoutBatchResponse.model_validate(batch),
        "payouts": [PayoutItemResponse.model_validate(payout) for payout in payouts],
    }


@router.post("/payout-batches", status_code=status.HTTP_201_CREATED)
async def create_payout_batch(
    body: PayoutBatchCreateRequest,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    batch, payouts = await finance.create_payout_batch(
        session,
        principal,
        program_id=body.program_id,
        cutoff_at=body.cutoff_at,
        scenario=body.scenario,
    )
    return _batch_payload(batch, payouts)


@router.post("/payout-batches/{batch_id}/approve")
async def approve_payout_batch(
    batch_id: uuid.UUID,
    body: ApprovalRequest,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    batch, payouts = await finance.approve_payout_batch(
        session, principal, batch_id=batch_id, comment=body.comment
    )
    return _batch_payload(batch, payouts)


@router.get("/payout-batches/{batch_id}")
async def get_payout_batch(
    batch_id: uuid.UUID,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    assert principal.brand_id is not None
    batch, payouts = await finance.get_batch(session, principal.brand_id, batch_id)
    return _batch_payload(batch, payouts)
