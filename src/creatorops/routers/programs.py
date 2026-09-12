import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, get_principal, require_roles
from creatorops.models.enums import BrandRole, UserKind
from creatorops.schemas import (
    CampaignCreateRequest,
    CampaignResponse,
    CampaignStatusRequest,
    CommissionPlanCreateRequest,
    CommissionPlanResponse,
    ProgramCreateRequest,
    ProgramResponse,
    ProgramStatusRequest,
    TermsCreateRequest,
    TermsResponse,
)
from creatorops.services import programs

router = APIRouter(tags=["programs"])
staff_program_manager = require_roles(BrandRole.OWNER, BrandRole.OPS)


@router.post("/programs", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(
    body: ProgramCreateRequest,
    principal: Principal = Depends(staff_program_manager),
    session: AsyncSession = Depends(get_session),
) -> ProgramResponse:
    return ProgramResponse.model_validate(await programs.create_program(session, principal, body))


@router.get("/programs", response_model=list[ProgramResponse])
async def list_programs(
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> list[ProgramResponse]:
    rows = (
        await programs.discover_programs(session)
        if principal.kind == UserKind.CREATOR
        else await programs.list_programs(session, principal.brand_id)  # type: ignore[arg-type]
    )
    return [ProgramResponse.model_validate(row) for row in rows]


@router.post("/programs/{program_id}/status", response_model=ProgramResponse)
async def change_program_status(
    program_id: uuid.UUID,
    body: ProgramStatusRequest,
    principal: Principal = Depends(staff_program_manager),
    session: AsyncSession = Depends(get_session),
) -> ProgramResponse:
    row = await programs.change_program_status(session, principal, program_id, body.status)
    return ProgramResponse.model_validate(row)


@router.post(
    "/programs/{program_id}/terms",
    response_model=TermsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def publish_terms(
    program_id: uuid.UUID,
    body: TermsCreateRequest,
    principal: Principal = Depends(staff_program_manager),
    session: AsyncSession = Depends(get_session),
) -> TermsResponse:
    row = await programs.publish_terms(session, principal, program_id, body)
    return TermsResponse.model_validate(row)


@router.post(
    "/programs/{program_id}/campaigns",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign(
    program_id: uuid.UUID,
    body: CampaignCreateRequest,
    principal: Principal = Depends(staff_program_manager),
    session: AsyncSession = Depends(get_session),
) -> CampaignResponse:
    row = await programs.create_campaign(session, principal, program_id, body)
    return CampaignResponse.model_validate(row)


@router.post("/campaigns/{campaign_id}/status", response_model=CampaignResponse)
async def change_campaign_status(
    campaign_id: uuid.UUID,
    body: CampaignStatusRequest,
    principal: Principal = Depends(staff_program_manager),
    session: AsyncSession = Depends(get_session),
) -> CampaignResponse:
    row = await programs.change_campaign_status(session, principal, campaign_id, body.status)
    return CampaignResponse.model_validate(row)


@router.post(
    "/programs/{program_id}/commission-plans",
    response_model=CommissionPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_commission_plan(
    program_id: uuid.UUID,
    body: CommissionPlanCreateRequest,
    principal: Principal = Depends(require_roles(BrandRole.OWNER, BrandRole.FINANCE)),
    session: AsyncSession = Depends(get_session),
) -> CommissionPlanResponse:
    row = await programs.create_commission_plan(session, principal, program_id, body)
    return CommissionPlanResponse.model_validate(row)
