import uuid

from fastapi import APIRouter, Cookie, Depends, Header, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.errors import UnauthorizedError
from creatorops.core.security import stable_hash, verify_hmac_signature
from creatorops.schemas import CommerceWebhookRequest, WebhookResponse
from creatorops.services import attribution

redirect_router = APIRouter(tags=["tracking"])
router = APIRouter(tags=["commerce"])


@redirect_router.get("/r/{code}", include_in_schema=True)
async def redirect_affiliate_link(
    code: str,
    request: Request,
    visitor: str | None = Query(default=None),
    creatorops_visitor: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    visitor_id = visitor or creatorops_visitor or uuid.uuid4().hex
    ip = request.client.host if request.client else "unknown"
    click, target = await attribution.register_click(
        session,
        code=code,
        visitor_id=visitor_id,
        user_agent=request.headers.get("user-agent"),
        ip_hash=stable_hash(ip),
    )
    response = RedirectResponse(target, status_code=307)
    response.set_cookie(
        "creatorops_visitor",
        visitor_id,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="lax",
    )
    response.headers["X-CreatorOps-Click-ID"] = str(click.id)
    return response


@router.post("/webhooks/commerce/{brand_slug}", response_model=WebhookResponse)
async def commerce_webhook(
    brand_slug: str,
    request: Request,
    signature: str | None = Header(default=None, alias="X-Webhook-Signature"),
    session: AsyncSession = Depends(get_session),
) -> WebhookResponse:
    raw = await request.body()
    if not verify_hmac_signature(raw, signature):
        raise UnauthorizedError("Invalid webhook signature")
    body = CommerceWebhookRequest.model_validate_json(raw)
    result = await attribution.process_commerce_webhook(
        session, brand_slug=brand_slug, request=body
    )
    return WebhookResponse.model_validate(result)
