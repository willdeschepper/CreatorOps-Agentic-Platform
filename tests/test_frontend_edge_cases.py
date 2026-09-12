import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from creatorops.core.db import session_factory
from creatorops.core.errors import ConflictError
from creatorops.core.security import Principal
from creatorops.models.enums import BrandRole, ContentStatus, UserKind
from creatorops.models.identity import User
from creatorops.models.listening import ContentEvidence
from creatorops.models.partnerships import CreatorApplication, CreatorInvitation
from creatorops.schemas import SocialPostInput
from creatorops.services.listening import ingest_social_post, review_content
from tests.helpers import auth, create_domain_fixture, post_webhook, unique


class MemoryStore:
    async def upsert(self, payload: dict[str, object]) -> str:
        return f"local/{payload['brand_id']}/{payload['external_post_id']}"


async def _register(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "CreatorOps123!", "display_name": "Test Creator"},
    )
    assert response.status_code == 201
    response = await client.post(
        "/v1/auth/token", json={"email": email, "password": "CreatorOps123!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_invitation_email_and_expiry(client: AsyncClient) -> None:
    fixture = await create_domain_fixture(creator_count=0)
    expected_email = f"{unique('invite')}@example.com"
    wrong_token = await _register(client, f"{unique('wrong')}@example.com")
    invited_token = await _register(client, expected_email)
    response = await client.post(
        f"/v1/programs/{fixture.program_id}/invitations",
        headers=auth(fixture.staff_token),
        json={"email": expected_email, "expires_in_hours": 1},
    )
    assert response.status_code == 201
    invitation = response.json()
    mismatch = await client.post(
        f"/v1/invitations/{invitation['token']}/accept", headers=auth(wrong_token)
    )
    assert mismatch.status_code == 409
    assert mismatch.json()["code"] == "invitation_email_mismatch"
    async with session_factory() as session, session.begin():
        row = await session.get(CreatorInvitation, uuid.UUID(invitation["id"]))
        assert row is not None
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    expired = await client.post(
        f"/v1/invitations/{invitation['token']}/accept", headers=auth(invited_token)
    )
    assert expired.status_code == 409
    assert expired.json()["code"] == "invitation_not_usable"
    assert (await client.get(f"/v1/invitations/{invitation['token']}")).json()[
        "status"
    ] == "expired"


async def test_finance_cannot_read_application_detail(client: AsyncClient) -> None:
    fixture = await create_domain_fixture(role=BrandRole.FINANCE, creator_count=1)
    async with session_factory() as session:
        application_id = await session.scalar(
            select(CreatorApplication.id).where(CreatorApplication.program_id == fixture.program_id)
        )
    assert application_id is not None
    response = await client.get(
        f"/v1/applications/{application_id}", headers=auth(fixture.staff_token)
    )
    assert response.status_code == 403


async def test_application_can_retry_after_withdrawal_and_rejection(
    client: AsyncClient,
) -> None:
    fixture = await create_domain_fixture(creator_count=0)
    creator_token = await _register(client, f"{unique('apply')}@example.com")
    path = f"/v1/programs/{fixture.program_id}/applications"
    first = await client.post(path, headers=auth(creator_token), json={"motivation": "First"})
    assert first.status_code == 201
    withdrawn = await client.post(
        f"/v1/applications/{first.json()['id']}/withdraw",
        headers=auth(creator_token),
        json={"comment": "Changing my application"},
    )
    assert withdrawn.status_code == 200
    assert withdrawn.json()["status"] == "withdrawn"
    second = await client.post(path, headers=auth(creator_token), json={"motivation": "Second"})
    assert second.status_code == 201
    assert second.json()["id"] != first.json()["id"]
    rejected = await client.post(
        f"/v1/applications/{second.json()['id']}/review",
        headers=auth(fixture.staff_token),
        json={"decision": "rejected", "review_note": "Try again"},
    )
    assert rejected.status_code == 200
    third = await client.post(path, headers=auth(creator_token), json={"motivation": "Third"})
    assert third.status_code == 201
    approved = await client.post(
        f"/v1/applications/{third.json()['id']}/review",
        headers=auth(fixture.staff_token),
        json={"decision": "approved", "review_note": "Ready"},
    )
    assert approved.status_code == 200
    blocked = await client.post(path, headers=auth(creator_token), json={"motivation": "Fourth"})
    assert blocked.status_code == 409


async def test_draft_batch_cancel_is_safe(client: AsyncClient) -> None:
    fixture = await create_domain_fixture(creator_count=1, return_window_days=0)
    creator = fixture.creators[0]
    now = datetime.now(UTC)
    paid = await post_webhook(
        client,
        fixture,
        {
            "event_id": unique("paid"),
            "event_type": "order.paid",
            "order_id": unique("order"),
            "occurred_at": now.isoformat(),
            "amount": "100.00",
            "currency": "BRL",
            "coupon_code": creator.coupon_code,
        },
    )
    assert paid.status_code == 200
    settled = await client.post(
        "/v1/commissions/settle",
        headers=auth(fixture.staff_token),
        json={"as_of": (now + timedelta(days=1)).isoformat()},
    )
    assert settled.status_code == 200
    batch = await client.post(
        "/v1/payout-batches",
        headers=auth(fixture.staff_token),
        json={
            "program_id": str(fixture.program_id),
            "cutoff_at": (now + timedelta(days=1, minutes=1)).isoformat(),
            "scenario": "success",
        },
    )
    assert batch.status_code == 201
    batch_id = batch.json()["batch"]["id"]
    amount = batch.json()["payouts"][0]["amount"]
    cancelled = await client.post(
        f"/v1/payout-batches/{batch_id}/cancel",
        headers=auth(fixture.staff_token),
        json={"comment": "Snapshot not needed"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["batch"]["status"] == "cancelled"
    replay = await client.post(
        f"/v1/payout-batches/{batch_id}/cancel",
        headers=auth(fixture.staff_token),
        json={"comment": "Safe replay"},
    )
    assert replay.status_code == 200
    assert replay.json()["payouts"][0]["amount"] == amount
    report = await client.get(
        f"/v1/reports/memberships/{creator.membership_id}/overview",
        headers=auth(await _token_for_creator(creator.user_id)),
    )
    assert report.status_code == 200
    assert report.json()["commission_available"] == amount


async def _token_for_creator(creator_id: uuid.UUID) -> str:
    from creatorops.core.security import create_access_token

    async with session_factory() as session:
        user = await session.get(User, creator_id)
        assert user is not None
        return create_access_token(user)


async def test_rejected_post_reimport_and_scope_change(client: AsyncClient) -> None:
    fixture = await create_domain_fixture(creator_count=1)
    creator = fixture.creators[0]
    async with session_factory() as session:
        from creatorops.models.identity import SocialProfile

        handle = await session.scalar(
            select(SocialProfile.handle).where(SocialProfile.creator_id == creator.user_id)
        )
    assert handle is not None
    external_post_id = unique("reviewed")
    published_at = datetime.now(UTC)
    store = MemoryStore()
    principal = Principal(
        user_id=fixture.staff_user_id,
        kind=UserKind.STAFF,
        brand_id=fixture.brand_id,
        role=BrandRole.OWNER,
    )

    def payload(views: int, *, changed_handle: bool = False) -> dict[str, Any]:
        post = SocialPostInput(
            network="instagram",
            external_post_id=external_post_id,
            handle="different_handle" if changed_handle else handle,
            program_id=fixture.program_id,
            published_at=published_at,
            metrics={"views": views},
        )
        return dict(post.model_dump(mode="json"), brand_id=str(fixture.brand_id))

    async with session_factory() as session, session.begin():
        content = await ingest_social_post(
            session,
            payload=payload(10),
            store=store,  # type: ignore[arg-type]
        )
        content_id = content.id
    async with session_factory() as session:
        rejected = await review_content(
            session, principal=principal, content_id=content_id, decision=ContentStatus.REJECTED
        )
        reviewed_at = rejected.reviewed_at
    async with session_factory() as session, session.begin():
        await ingest_social_post(
            session,
            payload=payload(50),
            store=store,  # type: ignore[arg-type]
        )
    async with session_factory() as session:
        row = await session.get(ContentEvidence, content_id)
        assert row is not None
        assert row.status == ContentStatus.REJECTED
        assert row.reviewed_by == fixture.staff_user_id
        assert row.reviewed_at == reviewed_at
        assert row.metrics["views"] == 50
    with pytest.raises(ConflictError):
        async with session_factory() as session, session.begin():
            await ingest_social_post(
                session,
                payload=payload(100, changed_handle=True),
                store=store,  # type: ignore[arg-type]
            )
