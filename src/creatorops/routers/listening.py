import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, require_roles
from creatorops.models.enums import BrandRole, ContentStatus
from creatorops.schemas import (
    ContentEvidenceResponse,
    ContentReviewRequest,
    SocialImportRequest,
)
from creatorops.services import listening

router = APIRouter(tags=["social-listening"])
ops_roles = require_roles(BrandRole.OWNER, BrandRole.OPS)


@router.post("/listening/imports", status_code=status.HTTP_202_ACCEPTED)
async def import_social_posts(
    body: SocialImportRequest,
    principal: Principal = Depends(ops_roles),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int | str]:
    queued = await listening.queue_social_import(session, principal=principal, posts=body.posts)
    return {"status": "queued", "posts": queued}


@router.get("/posts", response_model=list[ContentEvidenceResponse])
async def list_social_posts(
    content_status: ContentStatus | None = None,
    principal: Principal = Depends(ops_roles),
    session: AsyncSession = Depends(get_session),
) -> list[ContentEvidenceResponse]:
    assert principal.brand_id is not None
    rows = await listening.list_content(session, brand_id=principal.brand_id, status=content_status)
    return [ContentEvidenceResponse.model_validate(row) for row in rows]


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
