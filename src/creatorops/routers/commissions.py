import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.errors import NotFoundError
from creatorops.core.security import Principal, require_creator, require_roles
from creatorops.models.enums import BrandRole, LedgerBucket
from creatorops.models.partnerships import ProgramMembership
from creatorops.schemas import BalanceResponse, SettlementRequest
from creatorops.services import commissions

router = APIRouter(tags=["commissions"])


@router.post("/commissions/settle")
async def settle_commissions(
    body: SettlementRequest,
    _principal: Principal = Depends(require_roles(BrandRole.OWNER, BrandRole.FINANCE)),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    return {"settled": await commissions.settle_due_commissions(session, as_of=body.as_of)}


@router.get(
    "/memberships/{membership_id}/balance",
    response_model=BalanceResponse,
)
async def creator_balance(
    membership_id: uuid.UUID,
    principal: Principal = Depends(require_creator),
    session: AsyncSession = Depends(get_session),
) -> BalanceResponse:
    membership = await session.scalar(
        select(ProgramMembership).where(
            ProgramMembership.id == membership_id,
            ProgramMembership.creator_id == principal.user_id,
        )
    )
    if membership is None:
        raise NotFoundError("membership_not_found", "Creator membership was not found")
    balance = await commissions.balances_for_membership(session, membership_id)
    return BalanceResponse(
        membership_id=membership_id,
        pending=balance[LedgerBucket.PENDING],
        available=balance[LedgerBucket.AVAILABLE],
        reserved=balance[LedgerBucket.RESERVED],
        paid=balance[LedgerBucket.PAID],
    )
