import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, get_principal, require_roles
from creatorops.models.enums import BrandRole, CampaignStatus, ProgramStatus, UserKind
from creatorops.schemas import (
    BonusRuleResponse,
    CampaignCreateRequest,
    CampaignResponse,
    CampaignStatusRequest,
    CommissionPlanCreateRequest,
    CommissionPlanDetailResponse,
    CommissionPlanResponse,
    CommissionTierResponse,
    PageResponse,
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


@router.get("/programs", response_model=PageResponse[ProgramResponse])
async def list_programs(
    program_status: ProgramStatus | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[ProgramResponse]:
    rows, total = (
        await programs.discover_programs(session, limit=limit, offset=offset)
        if principal.kind == UserKind.CREATOR
        else await programs.list_programs(
            session,
            principal.brand_id,  # type: ignore[arg-type]
            status=program_status,
            limit=limit,
            offset=offset,
        )
    )
    return PageResponse(
        items=[ProgramResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/programs/{program_id}", response_model=ProgramResponse)
async def get_program(
    program_id: uuid.UUID,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> ProgramResponse:
    row = await programs.get_visible_program(session, principal=principal, program_id=program_id)
    return ProgramResponse.model_validate(row)


@router.get("/programs/{program_id}/campaigns", response_model=PageResponse[CampaignResponse])
async def list_campaigns(
    program_id: uuid.UUID,
    campaign_status: CampaignStatus | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[CampaignResponse]:
    rows, total = await programs.list_campaigns(
        session,
        principal=principal,
        program_id=program_id,
        status=campaign_status,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[CampaignResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: uuid.UUID,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> CampaignResponse:
    row = await programs.get_visible_campaign(session, principal=principal, campaign_id=campaign_id)
    return CampaignResponse.model_validate(row)


@router.get("/programs/{program_id}/terms", response_model=PageResponse[TermsResponse])
async def list_terms(
    program_id: uuid.UUID,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[TermsResponse]:
    rows, total = await programs.list_terms(
        session, principal=principal, program_id=program_id, limit=limit, offset=offset
    )
    return PageResponse(
        items=[TermsResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/programs/{program_id}/commission-plans",
    response_model=PageResponse[CommissionPlanResponse],
)
async def list_commission_plans(
    program_id: uuid.UUID,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[CommissionPlanResponse]:
    rows, total = await programs.list_commission_plans(
        session, principal=principal, program_id=program_id, limit=limit, offset=offset
    )
    return PageResponse(
        items=[CommissionPlanResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/commission-plans/{plan_id}", response_model=CommissionPlanDetailResponse)
async def get_commission_plan(
    plan_id: uuid.UUID,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> CommissionPlanDetailResponse:
    plan, tiers, bonuses = await programs.get_commission_plan_detail(
        session, principal=principal, plan_id=plan_id
    )
    return CommissionPlanDetailResponse(
        **CommissionPlanResponse.model_validate(plan).model_dump(),
        tiers=[CommissionTierResponse.model_validate(row) for row in tiers],
        bonuses=[BonusRuleResponse.model_validate(row) for row in bonuses],
    )


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
