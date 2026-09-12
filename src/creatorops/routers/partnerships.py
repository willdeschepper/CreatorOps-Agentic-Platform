import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, require_creator, require_roles
from creatorops.models.enums import ApplicationStatus, BrandRole
from creatorops.schemas import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationReviewRequest,
    AssetResponse,
    MembershipResponse,
    TermsAcceptanceRequest,
)
from creatorops.services import partnerships

router = APIRouter(tags=["partnerships"])


@router.post(
    "/programs/{program_id}/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply(
    program_id: uuid.UUID,
    body: ApplicationCreateRequest,
    principal: Principal = Depends(require_creator),
    session: AsyncSession = Depends(get_session),
) -> ApplicationResponse:
    row = await partnerships.apply_to_program(session, principal, program_id, body)
    return ApplicationResponse.model_validate(row)


@router.get("/applications", response_model=list[ApplicationResponse])
async def applications(
    application_status: ApplicationStatus | None = None,
    principal: Principal = Depends(require_roles(BrandRole.OWNER, BrandRole.OPS)),
    session: AsyncSession = Depends(get_session),
) -> list[ApplicationResponse]:
    assert principal.brand_id is not None
    rows = await partnerships.list_applications(
        session, principal.brand_id, status=application_status
    )
    return [ApplicationResponse.model_validate(row) for row in rows]


@router.post("/applications/{application_id}/review")
async def review_application(
    application_id: uuid.UUID,
    body: ApplicationReviewRequest,
    principal: Principal = Depends(require_roles(BrandRole.OWNER, BrandRole.OPS)),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    application, membership = await partnerships.review_application(
        session, principal, application_id, body
    )
    return {
        "application": ApplicationResponse.model_validate(application),
        "membership": MembershipResponse.model_validate(membership) if membership else None,
    }


@router.post("/memberships/{membership_id}/terms-acceptances")
async def accept_terms(
    membership_id: uuid.UUID,
    body: TermsAcceptanceRequest,
    request: Request,
    principal: Principal = Depends(require_creator),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    membership, assets = await partnerships.accept_terms(
        session,
        principal,
        membership_id,
        body.terms_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "membership": MembershipResponse.model_validate(membership),
        "assets": [AssetResponse.model_validate(asset) for asset in assets],
    }


@router.get("/memberships/me", response_model=list[MembershipResponse])
async def my_memberships(
    principal: Principal = Depends(require_creator),
    session: AsyncSession = Depends(get_session),
) -> list[MembershipResponse]:
    rows = await partnerships.list_creator_memberships(session, principal.user_id)
    return [MembershipResponse.model_validate(row) for row in rows]


@router.get("/memberships/{membership_id}/assets", response_model=list[AssetResponse])
async def membership_assets(
    membership_id: uuid.UUID,
    principal: Principal = Depends(require_creator),
    session: AsyncSession = Depends(get_session),
) -> list[AssetResponse]:
    rows = await partnerships.list_membership_assets(
        session, membership_id=membership_id, creator_id=principal.user_id
    )
    return [AssetResponse.model_validate(row) for row in rows]
