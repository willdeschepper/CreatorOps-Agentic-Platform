import hashlib
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.errors import ConflictError, NotFoundError, UnprocessableError
from creatorops.core.time import clock
from creatorops.models.attribution import (
    AffiliateClick,
    CommerceWebhookEvent,
    Order,
    OrderAttribution,
)
from creatorops.models.enums import (
    AssetType,
    AttributionReason,
    CommerceEventType,
    MembershipStatus,
    OrderStatus,
    WebhookProcessingStatus,
)
from creatorops.models.identity import Brand
from creatorops.models.partnerships import AffiliateAsset, ProgramMembership
from creatorops.models.programs import Program
from creatorops.schemas import CommerceWebhookRequest
from creatorops.services.commissions import (
    accrue_order_commissions,
    create_refund_adjustments,
    money,
)
from creatorops.services.shared import enqueue_event


def canonical_payload_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


async def register_click(
    session: AsyncSession,
    *,
    code: str,
    visitor_id: str,
    user_agent: str | None,
    ip_hash: str | None,
) -> tuple[AffiliateClick, str]:
    now = clock.now()
    async with session.begin():
        row = (
            await session.execute(
                select(AffiliateAsset, ProgramMembership, Program)
                .join(ProgramMembership, ProgramMembership.id == AffiliateAsset.membership_id)
                .join(Program, Program.id == ProgramMembership.program_id)
                .where(
                    AffiliateAsset.asset_type == AssetType.LINK,
                    AffiliateAsset.code == code,
                    AffiliateAsset.active.is_(True),
                    ProgramMembership.status == MembershipStatus.ACTIVE,
                )
            )
        ).first()
        if row is None:
            raise NotFoundError("affiliate_link_not_found", "Affiliate link is inactive or missing")
        asset, _membership, program = row
        click = AffiliateClick(
            asset_id=asset.id,
            visitor_id=visitor_id,
            clicked_at=now,
            expires_at=now + timedelta(days=program.attribution_window_days),
            user_agent=user_agent,
            ip_hash=ip_hash,
        )
        session.add(click)
        await session.flush()
    return click, asset.target_url or "http://localhost:8000/docs"


async def _resolve_attribution(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    coupon_code: str | None,
    click_id: uuid.UUID | None,
    occurred_at: datetime,
) -> tuple[
    ProgramMembership | None,
    AffiliateAsset | None,
    AffiliateClick | None,
    AttributionReason,
    dict[str, object],
]:
    signals: dict[str, object] = {
        "coupon_code": coupon_code,
        "click_id": str(click_id) if click_id else None,
    }
    coupon_asset: AffiliateAsset | None = None
    coupon_membership: ProgramMembership | None = None
    if coupon_code:
        coupon_row = (
            await session.execute(
                select(AffiliateAsset, ProgramMembership, Program)
                .join(ProgramMembership, ProgramMembership.id == AffiliateAsset.membership_id)
                .join(Program, Program.id == ProgramMembership.program_id)
                .where(
                    AffiliateAsset.asset_type == AssetType.COUPON,
                    AffiliateAsset.code == coupon_code,
                    AffiliateAsset.active.is_(True),
                    ProgramMembership.status == MembershipStatus.ACTIVE,
                    Program.brand_id == brand_id,
                )
            )
        ).first()
        if coupon_row:
            coupon_asset, coupon_membership, _ = coupon_row

    click: AffiliateClick | None = None
    click_asset: AffiliateAsset | None = None
    click_membership: ProgramMembership | None = None
    if click_id:
        click_row = (
            await session.execute(
                select(AffiliateClick, AffiliateAsset, ProgramMembership, Program)
                .join(AffiliateAsset, AffiliateAsset.id == AffiliateClick.asset_id)
                .join(ProgramMembership, ProgramMembership.id == AffiliateAsset.membership_id)
                .join(Program, Program.id == ProgramMembership.program_id)
                .where(
                    AffiliateClick.id == click_id,
                    AffiliateAsset.active.is_(True),
                    ProgramMembership.status == MembershipStatus.ACTIVE,
                    Program.brand_id == brand_id,
                )
            )
        ).first()
        if click_row:
            maybe_click, maybe_asset, maybe_membership, _ = click_row
            event_time = occurred_at
            if maybe_click.clicked_at <= event_time <= maybe_click.expires_at:
                click = maybe_click
                click_asset = maybe_asset
                click_membership = maybe_membership

    if coupon_membership and coupon_asset:
        signals["coupon_membership_id"] = str(coupon_membership.id)
        if click_membership:
            signals["click_membership_id"] = str(click_membership.id)
            signals["conflict"] = click_membership.id != coupon_membership.id
        return coupon_membership, coupon_asset, click, AttributionReason.COUPON, signals
    if click_membership and click_asset and click:
        signals["click_membership_id"] = str(click_membership.id)
        return click_membership, click_asset, click, AttributionReason.LAST_CLICK, signals
    return None, None, click, AttributionReason.UNATTRIBUTED, signals


async def process_commerce_webhook(
    session: AsyncSession,
    *,
    brand_slug: str,
    request: CommerceWebhookRequest,
) -> dict[str, object]:
    now = clock.now()
    payload = request.model_dump(mode="json")
    payload_hash = canonical_payload_hash(payload)
    event_uuid = uuid.uuid4()
    async with session.begin():
        brand = await session.scalar(select(Brand).where(Brand.slug == brand_slug))
        if brand is None:
            raise NotFoundError("brand_not_found", "Brand webhook endpoint was not found")
        insert_result = await session.execute(
            pg_insert(CommerceWebhookEvent)
            .values(
                id=event_uuid,
                brand_id=brand.id,
                provider="local-commerce",
                external_event_id=request.event_id,
                event_type=request.event_type,
                payload_hash=payload_hash,
                payload=payload,
                occurred_at=request.occurred_at,
                received_at=now,
                status=WebhookProcessingStatus.RECEIVED,
            )
            .on_conflict_do_nothing(index_elements=["brand_id", "provider", "external_event_id"])
            .returning(CommerceWebhookEvent.id)
        )
        inserted_id = insert_result.scalar_one_or_none()
        if inserted_id is None:
            existing = await session.scalar(
                select(CommerceWebhookEvent).where(
                    CommerceWebhookEvent.brand_id == brand.id,
                    CommerceWebhookEvent.provider == "local-commerce",
                    CommerceWebhookEvent.external_event_id == request.event_id,
                )
            )
            if existing is None:
                raise ConflictError("webhook_race", "Webhook conflict could not be resolved")
            if existing.payload_hash != payload_hash:
                raise ConflictError(
                    "webhook_payload_conflict",
                    "The event_id was already used with a different payload",
                )
            replay = dict(existing.response or {})
            replay["duplicate"] = True
            return replay

        event = await session.get(CommerceWebhookEvent, inserted_id)
        if event is None:
            raise UnprocessableError("webhook_not_persisted", "Webhook event was not persisted")

        order = await session.scalar(
            select(Order)
            .where(Order.brand_id == brand.id, Order.external_id == request.order_id)
            .with_for_update()
        )
        if order is None:
            if request.amount <= 0 and request.event_type in {
                CommerceEventType.CREATED,
                CommerceEventType.PAID,
            }:
                raise UnprocessableError("invalid_order_amount", "Order amount must be positive")
            order = Order(
                brand_id=brand.id,
                external_id=request.order_id,
                status=OrderStatus.CREATED,
                gross_amount=money(request.amount),
                currency=request.currency,
            )
            session.add(order)
            await session.flush()

        attribution = await session.scalar(
            select(OrderAttribution).where(OrderAttribution.order_id == order.id)
        )
        response: dict[str, object] = {
            "event_id": request.event_id,
            "order_id": str(order.id),
            "status": order.status.value,
            "duplicate": False,
        }

        if request.event_type == CommerceEventType.CREATED:
            if order.status == OrderStatus.CREATED:
                order.gross_amount = money(request.amount)
            else:
                event.status = WebhookProcessingStatus.IGNORED
                response["ignored_reason"] = "order_already_progressed"

        elif request.event_type == CommerceEventType.PAID:
            if order.status in {OrderStatus.CANCELLED, OrderStatus.REFUNDED}:
                event.status = WebhookProcessingStatus.IGNORED
                response["ignored_reason"] = "terminal_order_state"
            elif order.status in {OrderStatus.PAID, OrderStatus.PARTIALLY_REFUNDED}:
                event.status = WebhookProcessingStatus.IGNORED
                response["ignored_reason"] = "order_already_paid"
            else:
                order.gross_amount = money(request.amount)
                order.status = OrderStatus.PAID
                order.paid_at = request.occurred_at
                if attribution is None:
                    membership, selected_asset, click, reason, signals = await _resolve_attribution(
                        session,
                        brand_id=brand.id,
                        coupon_code=request.coupon_code,
                        click_id=request.click_id,
                        occurred_at=request.occurred_at,
                    )
                    attribution = OrderAttribution(
                        order_id=order.id,
                        membership_id=membership.id if membership else None,
                        campaign_id=selected_asset.campaign_id if selected_asset else None,
                        coupon_asset_id=(
                            selected_asset.id
                            if reason == AttributionReason.COUPON and selected_asset
                            else None
                        ),
                        click_id=click.id if click else None,
                        reason=reason,
                        signals=signals,
                        attributed_at=now,
                    )
                    if membership:
                        order.program_id = membership.program_id
                    session.add(attribution)
                    await session.flush()
                commissions = await accrue_order_commissions(
                    session,
                    order=order,
                    attribution=attribution,
                    source_event_id=event.id,
                    occurred_at=request.occurred_at,
                )
                response["attribution"] = attribution.reason.value
                response["commission"] = str(
                    money(sum((item.amount for item in commissions), Decimal("0.00")))
                )
                enqueue_event(
                    session,
                    aggregate_type="order",
                    aggregate_id=order.id,
                    event_type="order.attributed",
                    payload={
                        "order_id": str(order.id),
                        "brand_id": str(brand.id),
                        "membership_id": (
                            str(attribution.membership_id) if attribution.membership_id else None
                        ),
                        "reason": attribution.reason.value,
                    },
                    now=now,
                )

        elif request.event_type in {CommerceEventType.CANCELLED, CommerceEventType.REFUNDED}:
            if (
                order.status == OrderStatus.CREATED
                and request.event_type == CommerceEventType.CANCELLED
            ):
                order.status = OrderStatus.CANCELLED
            elif order.status not in {
                OrderStatus.PAID,
                OrderStatus.PARTIALLY_REFUNDED,
            }:
                event.status = WebhookProcessingStatus.IGNORED
                response["ignored_reason"] = "refund_requires_paid_order"
            else:
                target_refunded = (
                    order.gross_amount
                    if request.event_type == CommerceEventType.CANCELLED
                    else money(request.refunded_amount or Decimal("0.00"))
                )
                if target_refunded > order.gross_amount:
                    raise UnprocessableError(
                        "refund_exceeds_order", "Refund cannot exceed the order gross amount"
                    )
                delta = money(target_refunded - order.refunded_amount)
                if delta <= 0:
                    event.status = WebhookProcessingStatus.IGNORED
                    response["ignored_reason"] = "refund_not_increasing"
                else:
                    order.refunded_amount = target_refunded
                    order.status = (
                        OrderStatus.REFUNDED
                        if target_refunded == order.gross_amount
                        else OrderStatus.PARTIALLY_REFUNDED
                    )
                    await create_refund_adjustments(
                        session,
                        order=order,
                        source_event_id=event.id,
                        refund_delta=delta,
                        occurred_at=request.occurred_at,
                    )

        if event.status == WebhookProcessingStatus.RECEIVED:
            event.status = WebhookProcessingStatus.PROCESSED
        event.order_id = order.id
        response["status"] = order.status.value
        event.response = response
    return response
