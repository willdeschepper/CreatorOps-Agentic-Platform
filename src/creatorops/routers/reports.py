import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, require_roles
from creatorops.models.enums import BrandRole
from creatorops.schemas import ReportOverviewResponse
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
