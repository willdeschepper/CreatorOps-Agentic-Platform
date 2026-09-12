import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from httpx import AsyncClient
from sqlalchemy import func, select

from creatorops.core.db import session_factory
from creatorops.core.security import Principal, create_access_token
from creatorops.models.enums import BrandRole, ContentStatus, UserKind
from creatorops.models.identity import User
from creatorops.models.listening import ContentEvidence
from creatorops.models.partnerships import AffiliateAsset, CampaignParticipant
from creatorops.schemas import SocialPostInput
from creatorops.services.listening import ingest_social_post, review_content
from tests.helpers import auth, create_domain_fixture, post_webhook, unique


class MemorySocialStore:
    def __init__(self) -> None:
        self.paths: list[str] = []

    async def upsert(self, payload: dict[str, object]) -> str:
        path = (
            f"social_posts/{payload['brand_id']}:{payload['network']}:{payload['external_post_id']}"
        )
        self.paths.append(path)
        return path


async def _creator_token(user_id: uuid.UUID) -> str:
    async with session_factory() as session:
        creator = await session.get(User, user_id)
        assert creator is not None
        return create_access_token(creator)


async def test_cors_pagination_and_tenant_reads(client: AsyncClient) -> None:
    tenant_a = await create_domain_fixture(creator_count=1)
    tenant_b = await create_domain_fixture(creator_count=1)
    preflight = await client.options(
        "/v1/programs",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"
    denied_origin = await client.options(
        "/v1/programs",
        headers={
            "Origin": "https://example.org",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert denied_origin.headers.get("access-control-allow-origin") is None

    page = await client.get("/v1/programs?limit=1&offset=0", headers=auth(tenant_a.staff_token))
    assert page.status_code == 200
    assert set(page.json()) == {"items", "total", "limit", "offset"}
    assert page.json()["items"][0]["id"] == str(tenant_a.program_id)
    assert page.json()["limit"] == 1
    assert (
        await client.get(f"/v1/programs/{tenant_b.program_id}", headers=auth(tenant_a.staff_token))
    ).status_code == 404
    assert (
        await client.get(
            f"/v1/programs/{tenant_b.program_id}/memberships",
            headers=auth(tenant_a.staff_token),
        )
    ).status_code == 404
    assert (await client.get("/v1/audit-logs", headers=auth(tenant_a.staff_token))).json()[
        "total"
    ] >= 0


async def test_invitation_acceptance_is_idempotent_and_revocation_blocks(
    client: AsyncClient,
) -> None:
    fixture = await create_domain_fixture(creator_count=1)
    creator = fixture.creators[0]
    creator_token = await _creator_token(creator.user_id)
    async with session_factory() as session:
        creator_user = await session.get(User, creator.user_id)
        assert creator_user is not None
        creator_email = creator_user.email
    # Existing membership is not invitable.
    conflict = await client.post(
        f"/v1/programs/{fixture.program_id}/invitations",
        headers=auth(fixture.staff_token),
        json={"email": creator_email},
    )
    assert conflict.status_code == 409

    email = f"{unique('invite')}@example.com"
    registered = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "CreatorOps123!", "display_name": "Invited User"},
    )
    assert registered.status_code == 201
    token = (
        await client.post("/v1/auth/token", json={"email": email, "password": "CreatorOps123!"})
    ).json()["access_token"]
    created = await client.post(
        f"/v1/programs/{fixture.program_id}/invitations",
        headers=auth(fixture.staff_token),
        json={"email": email},
    )
    assert created.status_code == 201
    invitation = created.json()
    assert invitation["token"] not in str(
        (
            await client.get(
                f"/v1/programs/{fixture.program_id}/invitations", headers=auth(fixture.staff_token)
            )
        ).json()
    )
    assert (await client.get(f"/v1/invitations/{invitation['token']}")).status_code == 200
    first, replay = await asyncio.gather(
        *(
            client.post(f"/v1/invitations/{invitation['token']}/accept", headers=auth(token))
            for _ in range(2)
        )
    )
    assert first.status_code == replay.status_code == 200
    assert first.json()["membership"]["id"] == replay.json()["membership"]["id"]
    assert first.json()["membership"]["status"] == "awaiting_terms"
    assert (
        await client.post(
            f"/v1/invitations/{invitation['id']}/revoke",
            headers=auth(fixture.staff_token),
            json={"comment": "Already accepted"},
        )
    ).status_code == 409

    second = await client.post(
        f"/v1/programs/{fixture.program_id}/invitations",
        headers=auth(fixture.staff_token),
        json={"email": f"{unique('revoked')}@example.com"},
    )
    assert second.status_code == 201
    revoked = await client.post(
        f"/v1/invitations/{second.json()['id']}/revoke",
        headers=auth(fixture.staff_token),
        json={"comment": "Cancelled invitation"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert (
        await client.post(
            f"/v1/invitations/{second.json()['token']}/accept", headers=auth(creator_token)
        )
    ).status_code == 409


async def test_campaign_selection_attribution_and_status(client: AsyncClient) -> None:
    fixture = await create_domain_fixture(creator_count=1, base_rate=Decimal("0.10"))
    creator = fixture.creators[0]
    now = datetime.now(UTC)
    campaign = await client.post(
        f"/v1/programs/{fixture.program_id}/campaigns",
        headers=auth(fixture.staff_token),
        json={
            "name": unique("Campaign"),
            "briefing": "Selected creators only",
            "starts_at": (now - timedelta(minutes=1)).isoformat(),
            "ends_at": (now + timedelta(days=1)).isoformat(),
        },
    )
    assert campaign.status_code == 201
    campaign_id = campaign.json()["id"]
    assert (
        await client.post(
            f"/v1/campaigns/{campaign_id}/status",
            headers=auth(fixture.staff_token),
            json={"status": "active"},
        )
    ).status_code == 200
    plan = await client.post(
        f"/v1/programs/{fixture.program_id}/commission-plans",
        headers=auth(fixture.staff_token),
        json={
            "campaign_id": campaign_id,
            "base_rate": "0.20",
            "return_window_days": 0,
            "payout_minimum": "1.00",
            "active_from": (now - timedelta(days=1)).isoformat(),
        },
    )
    assert plan.status_code == 201
    selected = await client.post(
        f"/v1/campaigns/{campaign_id}/participants",
        headers=auth(fixture.staff_token),
        json={"membership_ids": [str(creator.membership_id)]},
    )
    replay = await client.post(
        f"/v1/campaigns/{campaign_id}/participants",
        headers=auth(fixture.staff_token),
        json={"membership_ids": [str(creator.membership_id)]},
    )
    assert selected.status_code == replay.status_code == 201
    assert selected.json()[0]["id"] == replay.json()[0]["id"]
    async with session_factory() as session:
        assets = list(
            (
                await session.scalars(
                    select(AffiliateAsset).where(
                        AffiliateAsset.membership_id == creator.membership_id,
                        AffiliateAsset.campaign_id == uuid.UUID(campaign_id),
                    )
                )
            ).all()
        )
        assert len(assets) == 2
        coupon = next(asset for asset in assets if asset.asset_type.value == "coupon")
    paid = await post_webhook(
        client,
        fixture,
        {
            "event_id": unique("campaign-paid"),
            "event_type": "order.paid",
            "order_id": unique("campaign-order"),
            "occurred_at": now.isoformat(),
            "amount": "100.00",
            "currency": "BRL",
            "coupon_code": coupon.code,
        },
    )
    assert paid.status_code == 200
    assert paid.json()["commission"] == "20.00"
    campaign_report = await client.get(
        f"/v1/reports/campaigns/{campaign_id}/overview",
        headers=auth(fixture.staff_token),
    )
    assert campaign_report.status_code == 200
    assert campaign_report.json()["gmv"] == "100.00"
    assert campaign_report.json()["selected_creators"] == 1
    async with session_factory() as session:
        participants = await session.scalar(
            select(func.count(CampaignParticipant.id)).where(
                CampaignParticipant.campaign_id == uuid.UUID(campaign_id)
            )
        )
        assert participants == 1
    removed = await client.post(
        f"/v1/campaigns/{campaign_id}/participants/{creator.membership_id}/status",
        headers=auth(fixture.staff_token),
        json={"status": "removed", "comment": "Campaign scope changed"},
    )
    assert removed.status_code == 200
    assert removed.json()["status"] == "removed"
    second_paid = await post_webhook(
        client,
        fixture,
        {
            "event_id": unique("campaign-paid-later"),
            "event_type": "order.paid",
            "order_id": unique("campaign-order-later"),
            "occurred_at": now.isoformat(),
            "amount": "100.00",
            "currency": "BRL",
            "coupon_code": coupon.code,
        },
    )
    assert second_paid.status_code == 200
    assert second_paid.json()["attribution"] == "unattributed"


async def test_reviewed_social_reimport_preserves_human_decision_and_tenant() -> None:
    fixture_a = await create_domain_fixture(creator_count=1)
    fixture_b = await create_domain_fixture(creator_count=1)
    creator = fixture_a.creators[0]
    async with session_factory() as session:
        from creatorops.models.identity import SocialProfile

        handle = await session.scalar(
            select(SocialProfile.handle).where(SocialProfile.creator_id == creator.user_id)
        )
    assert handle is not None
    now = datetime.now(UTC)
    external_id = unique("social")
    store = MemorySocialStore()

    def payload(brand_id: uuid.UUID, views: int) -> dict[str, Any]:
        post = SocialPostInput(
            network="instagram",
            external_post_id=external_id,
            handle=handle,
            program_id=fixture_a.program_id
            if brand_id == fixture_a.brand_id
            else fixture_b.program_id,
            published_at=now,
            metrics={"views": views},
        )
        return dict(post.model_dump(mode="json"), brand_id=str(brand_id))

    async with session_factory() as session, session.begin():
        initial = await ingest_social_post(
            session, payload=payload(fixture_a.brand_id, 10), store=store
        )  # type: ignore[arg-type]
        initial_id = initial.id
    assert initial.status == ContentStatus.MATCHED
    principal = Principal(
        user_id=fixture_a.staff_user_id,
        kind=UserKind.STAFF,
        brand_id=fixture_a.brand_id,
        role=BrandRole.OWNER,
    )
    async with session_factory() as session:
        reviewed = await review_content(
            session, principal=principal, content_id=initial_id, decision=ContentStatus.APPROVED
        )
        reviewed_at = reviewed.reviewed_at
    async with session_factory() as session, session.begin():
        await ingest_social_post(session, payload=payload(fixture_a.brand_id, 20), store=store)  # type: ignore[arg-type]
    async with session_factory() as session, session.begin():
        tenant_b = await ingest_social_post(
            session, payload=payload(fixture_b.brand_id, 30), store=store
        )  # type: ignore[arg-type]
        assert tenant_b.id != initial_id
    async with session_factory() as session:
        updated = await session.get(ContentEvidence, initial_id)
        assert updated is not None
        assert updated.metrics["views"] == 20
        assert updated.status == ContentStatus.APPROVED
        assert updated.membership_id == creator.membership_id
        assert updated.reviewed_by == fixture_a.staff_user_id
        assert updated.reviewed_at == reviewed_at
        assert store.paths[0] != store.paths[-1]
        count = await session.scalar(
            select(func.count(ContentEvidence.id)).where(
                ContentEvidence.network == "instagram",
                ContentEvidence.external_post_id == external_id,
            )
        )
        assert count == 2
