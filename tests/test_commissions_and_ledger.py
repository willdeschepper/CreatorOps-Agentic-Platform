from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError

from creatorops.core.db import session_factory
from creatorops.models.commissions import LedgerEntry
from creatorops.models.enums import LedgerBucket, LedgerEntryType
from creatorops.services.commissions import balances_for_membership, settle_due_commissions
from tests.helpers import create_domain_fixture, post_webhook, unique


async def test_partial_refund_before_and_after_settlement(client: AsyncClient) -> None:
    fixture = await create_domain_fixture(
        creator_count=1,
        base_rate=Decimal("0.10"),
        return_window_days=7,
    )
    creator = fixture.creators[0]
    now = datetime.now(UTC)
    order_id = unique("refund-order")
    paid = {
        "event_id": unique("paid"),
        "event_type": "order.paid",
        "order_id": order_id,
        "occurred_at": now.isoformat(),
        "amount": "100.00",
        "currency": "BRL",
        "coupon_code": creator.coupon_code,
    }
    assert (await post_webhook(client, fixture, paid)).status_code == 200

    refund_before = {
        "event_id": unique("refund-before"),
        "event_type": "order.refunded",
        "order_id": order_id,
        "occurred_at": (now + timedelta(days=1)).isoformat(),
        "amount": "100.00",
        "currency": "BRL",
        "refunded_amount": "40.00",
    }
    assert (await post_webhook(client, fixture, refund_before)).status_code == 200
    async with session_factory() as session:
        balance = await balances_for_membership(session, creator.membership_id)
        assert balance[LedgerBucket.PENDING] == Decimal("6.00")

    async with session_factory() as session:
        assert (await settle_due_commissions(session, as_of=now + timedelta(days=8))) >= 2
    async with session_factory() as session:
        balance = await balances_for_membership(session, creator.membership_id)
        assert balance[LedgerBucket.PENDING] == Decimal("0.00")
        assert balance[LedgerBucket.AVAILABLE] == Decimal("6.00")

    refund_after = dict(
        refund_before,
        event_id=unique("refund-after"),
        occurred_at=(now + timedelta(days=9)).isoformat(),
        refunded_amount="60.00",
    )
    assert (await post_webhook(client, fixture, refund_after)).status_code == 200
    async with session_factory() as session:
        balance = await balances_for_membership(session, creator.membership_id)
        assert balance[LedgerBucket.AVAILABLE] == Decimal("4.00")


async def test_database_rejects_ledger_mutation() -> None:
    fixture = await create_domain_fixture(creator_count=1)
    creator = fixture.creators[0]
    async with session_factory() as session, session.begin():
        from creatorops.services.commissions import add_ledger_entry

        add_ledger_entry(
            session,
            brand_id=fixture.brand_id,
            program_id=fixture.program_id,
            membership_id=creator.membership_id,
            bucket=LedgerBucket.AVAILABLE,
            entry_type=LedgerEntryType.RECONCILIATION_ADJUSTMENT,
            amount=Decimal("10.00"),
            idempotency_key=unique("append-only"),
            description="Append-only trigger test",
        )

    async with session_factory() as session:
        entry_id = await session.scalar(
            select(LedgerEntry.id).where(LedgerEntry.membership_id == creator.membership_id)
        )
    assert entry_id is not None
    with pytest.raises(DBAPIError, match="append-only"):
        async with session_factory() as session, session.begin():
            await session.execute(
                update(LedgerEntry)
                .where(LedgerEntry.id == entry_id)
                .values(description="illegal rewrite")
            )
