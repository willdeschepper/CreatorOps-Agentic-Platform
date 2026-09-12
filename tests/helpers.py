import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from httpx import AsyncClient, Response

from creatorops.core.config import settings
from creatorops.core.db import session_factory
from creatorops.core.security import create_access_token, hash_password
from creatorops.models.commissions import CommissionPlan, CommissionTier
from creatorops.models.enums import (
    ApplicationSource,
    ApplicationStatus,
    AssetType,
    BrandRole,
    MembershipStatus,
    ProgramStatus,
    SocialNetwork,
    UserKind,
)
from creatorops.models.identity import Brand, BrandMembership, SocialProfile, User
from creatorops.models.partnerships import AffiliateAsset, CreatorApplication, ProgramMembership
from creatorops.models.programs import Program


@dataclass(frozen=True, slots=True)
class CreatorFixture:
    user_id: uuid.UUID
    membership_id: uuid.UUID
    coupon_code: str
    link_code: str


@dataclass(frozen=True, slots=True)
class DomainFixture:
    brand_id: uuid.UUID
    brand_slug: str
    staff_user_id: uuid.UUID
    staff_email: str
    staff_token: str
    role: BrandRole
    program_id: uuid.UUID
    plan_id: uuid.UUID
    creators: tuple[CreatorFixture, ...]


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


async def create_domain_fixture(
    *,
    role: BrandRole = BrandRole.OWNER,
    creator_count: int = 1,
    base_rate: Decimal = Decimal("0.10"),
    tier_rate: Decimal | None = None,
    return_window_days: int = 7,
    payout_minimum: Decimal = Decimal("1.00"),
) -> DomainFixture:
    now = datetime.now(UTC)
    brand_slug = unique("brand")
    staff_email = f"{unique(role.value)}@example.com"
    async with session_factory() as session, session.begin():
        brand = Brand(name=f"Brand {brand_slug}", slug=brand_slug)
        staff = User(
            email=staff_email,
            password_hash=hash_password("CreatorOps123!"),
            display_name="Local Staff",
            kind=UserKind.STAFF,
        )
        session.add_all([brand, staff])
        await session.flush()
        session.add(BrandMembership(brand_id=brand.id, user_id=staff.id, role=role))
        program = Program(
            brand_id=brand.id,
            name="Creator Program",
            slug=unique("program"),
            status=ProgramStatus.ACTIVE,
            attribution_window_days=30,
            return_window_days=return_window_days,
            payout_minimum=payout_minimum,
            currency="BRL",
        )
        session.add(program)
        await session.flush()
        plan = CommissionPlan(
            program_id=program.id,
            campaign_id=None,
            version=1,
            base_rate=base_rate,
            return_window_days=return_window_days,
            payout_minimum=payout_minimum,
            active_from=now - timedelta(days=1),
        )
        session.add(plan)
        await session.flush()
        if tier_rate is not None:
            session.add(
                CommissionTier(
                    plan_id=plan.id,
                    threshold_gmv=Decimal("100.00"),
                    rate=tier_rate,
                )
            )

        creators: list[CreatorFixture] = []
        for index in range(creator_count):
            social_handle = f"creator_{uuid.uuid4().hex[:10]}"
            creator = User(
                email=f"{unique(f'creator-{index}')}@example.com",
                password_hash=hash_password("CreatorOps123!"),
                display_name=f"Creator {index}",
                kind=UserKind.CREATOR,
            )
            session.add(creator)
            await session.flush()
            session.add(
                SocialProfile(
                    creator_id=creator.id,
                    network=SocialNetwork.INSTAGRAM,
                    handle=social_handle,
                    handle_normalized=social_handle,
                    verified=True,
                )
            )
            application = CreatorApplication(
                program_id=program.id,
                creator_id=creator.id,
                source=ApplicationSource.SELF,
                status=ApplicationStatus.APPROVED,
                motivation="Integration test",
                reviewed_by=staff.id,
                reviewed_at=now,
            )
            session.add(application)
            await session.flush()
            membership = ProgramMembership(
                program_id=program.id,
                creator_id=creator.id,
                application_id=application.id,
                status=MembershipStatus.ACTIVE,
                activated_at=now,
                version=1,
            )
            session.add(membership)
            await session.flush()
            coupon_code = unique("COUPON").upper()
            link_code = unique("link")
            session.add_all(
                [
                    AffiliateAsset(
                        membership_id=membership.id,
                        asset_type=AssetType.COUPON,
                        code=coupon_code,
                        active=True,
                    ),
                    AffiliateAsset(
                        membership_id=membership.id,
                        asset_type=AssetType.LINK,
                        code=link_code,
                        target_url="http://testserver/docs",
                        active=True,
                    ),
                ]
            )
            creators.append(
                CreatorFixture(
                    user_id=creator.id,
                    membership_id=membership.id,
                    coupon_code=coupon_code,
                    link_code=link_code,
                )
            )
        token = create_access_token(staff, brand_id=brand.id, role=role)
        fixture = DomainFixture(
            brand_id=brand.id,
            brand_slug=brand.slug,
            staff_user_id=staff.id,
            staff_email=staff.email,
            staff_token=token,
            role=role,
            program_id=program.id,
            plan_id=plan.id,
            creators=tuple(creators),
        )
    return fixture


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def post_webhook(
    client: AsyncClient, fixture: DomainFixture, payload: dict[str, Any]
) -> Response:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(settings.commerce_webhook_secret.encode(), raw, hashlib.sha256).hexdigest()
    return await client.post(
        f"/v1/webhooks/commerce/{fixture.brand_slug}",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
        },
    )
