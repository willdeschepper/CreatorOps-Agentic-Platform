import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import func, select

from creatorops.core.db import session_factory
from creatorops.models.attribution import CommerceWebhookEvent, Order, OrderAttribution
from creatorops.models.commissions import Commission
from tests.helpers import create_domain_fixture, post_webhook, unique


async def test_coupon_wins_conflicting_link_and_replay_is_idempotent(
    client: AsyncClient,
) -> None:
    fixture = await create_domain_fixture(
        creator_count=2,
        base_rate=Decimal("0.10"),
        tier_rate=Decimal("0.12"),
    )
    coupon_creator, link_creator = fixture.creators
    click = await client.get(f"/r/{link_creator.link_code}?visitor=test-shopper")
    assert click.status_code == 307

    now = datetime.now(UTC)
    payload = {
        "event_id": unique("evt"),
        "event_type": "order.paid",
        "order_id": unique("order"),
        "occurred_at": now.isoformat(),
        "amount": "200.00",
        "currency": "BRL",
        "coupon_code": coupon_creator.coupon_code,
        "click_id": click.headers["X-CreatorOps-Click-ID"],
    }
    first = await post_webhook(client, fixture, payload)
    replay = await post_webhook(client, fixture, payload)
    assert first.status_code == 200
    assert first.json()["attribution"] == "coupon"
    assert first.json()["commission"] == "24.00"
    assert replay.status_code == 200
    assert replay.json()["duplicate"] is True

    changed = dict(payload, amount="201.00")
    conflict = await post_webhook(client, fixture, changed)
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "webhook_payload_conflict"

    late_created = dict(
        payload,
        event_id=unique("evt-late"),
        event_type="order.created",
        occurred_at=(now - timedelta(minutes=10)).isoformat(),
        amount="999.00",
    )
    late = await post_webhook(client, fixture, late_created)
    assert late.status_code == 200
    assert late.json()["status"] == "paid"

    async with session_factory() as session:
        row = (
            await session.execute(
                select(Order, OrderAttribution)
                .join(OrderAttribution, OrderAttribution.order_id == Order.id)
                .where(Order.external_id == payload["order_id"])
            )
        ).one()
        order, attribution = row
        assert order.gross_amount == Decimal("200.00")
        assert attribution.membership_id == coupon_creator.membership_id
        assert attribution.signals["conflict"] is True
        commission_count = await session.scalar(
            select(func.count(Commission.id)).where(Commission.order_id == order.id)
        )
        assert commission_count == 1


async def test_concurrent_webhook_delivery_creates_one_effect(client: AsyncClient) -> None:
    fixture = await create_domain_fixture(creator_count=1)
    creator = fixture.creators[0]
    payload = {
        "event_id": unique("evt-concurrent"),
        "event_type": "order.paid",
        "order_id": unique("order-concurrent"),
        "occurred_at": datetime.now(UTC).isoformat(),
        "amount": "80.00",
        "currency": "BRL",
        "coupon_code": creator.coupon_code,
    }
    responses = await asyncio.gather(*(post_webhook(client, fixture, payload) for _ in range(8)))
    assert {response.status_code for response in responses} == {200}
    assert sum(response.json()["duplicate"] is False for response in responses) == 1
    assert sum(response.json()["duplicate"] is True for response in responses) == 7

    async with session_factory() as session:
        webhook_count = await session.scalar(
            select(func.count(CommerceWebhookEvent.id)).where(
                CommerceWebhookEvent.external_event_id == payload["event_id"]
            )
        )
        order_count = await session.scalar(
            select(func.count(Order.id)).where(Order.external_id == payload["order_id"])
        )
        assert webhook_count == 1
        assert order_count == 1
