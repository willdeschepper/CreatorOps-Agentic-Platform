import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, get_principal, require_roles
from creatorops.models.enums import BrandRole
from creatorops.schemas import (
    CampaignReportResponse,
    MembershipReportResponse,
    ReportOverviewResponse,
)
from creatorops.services import reporting

router = APIRouter(tags=["reporting"])


@router.get("/reports/programs/{program_id}/overview", response_model=ReportOverviewResponse)
async def program_overview(
    program_id: uuid.UUID,
    principal: Principal = Depends(
        require_roles(BrandRole.OWNER, BrandRole.OPS, BrandRole.FINANCE)
    ),
    session: AsyncSession = Depends(get_session),
) -> ReportOverviewResponse:
    assert principal.brand_id is not None
    return await reporting.program_overview(
        session, brand_id=principal.brand_id, program_id=program_id
    )


@router.get("/reports/campaigns/{campaign_id}/overview", response_model=CampaignReportResponse)
async def campaign_overview(
    campaign_id: uuid.UUID,
    principal: Principal = Depends(
        require_roles(BrandRole.OWNER, BrandRole.OPS, BrandRole.FINANCE)
    ),
    session: AsyncSession = Depends(get_session),
) -> CampaignReportResponse:
    assert principal.brand_id is not None
    return await reporting.campaign_overview(
        session, brand_id=principal.brand_id, campaign_id=campaign_id
    )


@router.get(
    "/reports/memberships/{membership_id}/overview",
    response_model=MembershipReportResponse,
)
async def membership_overview(
    membership_id: uuid.UUID,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> MembershipReportResponse:
    return await reporting.membership_overview(
        session, principal=principal, membership_id=membership_id
    )
