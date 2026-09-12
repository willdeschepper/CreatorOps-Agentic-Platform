import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, require_roles
from creatorops.models.enums import BrandRole, ContentStatus
from creatorops.schemas import (
    ContentEvidenceDetailResponse,
    ContentEvidenceResponse,
    ContentReviewRequest,
    PageResponse,
    SocialImportRequest,
    SocialImportResponse,
)
from creatorops.services import listening

router = APIRouter(tags=["social-listening"])
ops_roles = require_roles(BrandRole.OWNER, BrandRole.OPS)


@router.post(
    "/listening/imports",
    response_model=SocialImportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def import_social_posts(
    body: SocialImportRequest,
    principal: Principal = Depends(ops_roles),
    session: AsyncSession = Depends(get_session),
) -> SocialImportResponse:
    queued = await listening.queue_social_import(session, principal=principal, posts=body.posts)
    return SocialImportResponse(status="queued", posts=queued)


@router.get("/posts", response_model=PageResponse[ContentEvidenceResponse])
async def list_social_posts(
    content_status: ContentStatus | None = None,
    program_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    membership_id: uuid.UUID | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(ops_roles),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[ContentEvidenceResponse]:
    assert principal.brand_id is not None
    rows, total = await listening.list_content(
        session,
        brand_id=principal.brand_id,
        status=content_status,
        program_id=program_id,
        campaign_id=campaign_id,
        membership_id=membership_id,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[ContentEvidenceResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/posts/{content_id}", response_model=ContentEvidenceDetailResponse)
async def get_social_post(
    content_id: uuid.UUID,
    principal: Principal = Depends(ops_roles),
    session: AsyncSession = Depends(get_session),
) -> ContentEvidenceDetailResponse:
    assert principal.brand_id is not None
    row = await listening.get_content(session, brand_id=principal.brand_id, content_id=content_id)
    return ContentEvidenceDetailResponse.model_validate(row)


@router.post("/posts/{content_id}/review", response_model=ContentEvidenceResponse)
async def review_social_post(
    content_id: uuid.UUID,
    body: ContentReviewRequest,
    principal: Principal = Depends(ops_roles),
    session: AsyncSession = Depends(get_session),
) -> ContentEvidenceResponse:
    row = await listening.review_content(
        session,
        principal=principal,
        content_id=content_id,
        decision=ContentStatus(body.decision),
    )
    return ContentEvidenceResponse.model_validate(row)
