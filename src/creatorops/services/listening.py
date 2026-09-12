import uuid
from typing import Any, cast

from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.config import settings
from creatorops.core.errors import NotFoundError
from creatorops.core.security import Principal
from creatorops.core.time import clock
from creatorops.models.enums import ContentStatus, MembershipStatus
from creatorops.models.identity import SocialProfile
from creatorops.models.listening import ContentEvidence
from creatorops.models.partnerships import ProgramMembership
from creatorops.models.programs import Campaign, Program
from creatorops.schemas import SocialPostInput
from creatorops.services.programs import get_program_for_brand
from creatorops.services.shared import enqueue_event, normalize_handle


class FirestoreListeningStore:
    def __init__(self) -> None:
        if settings.app_env == "local" and not settings.firestore_emulator_host:
            raise RuntimeError("Local mode refuses to start without Firestore Emulator")
        self.client = firestore.AsyncClient(
            project=settings.local_project_id,
            credentials=AnonymousCredentials(),  # type: ignore[no-untyped-call]
        )

    async def upsert(self, payload: dict[str, object]) -> str:
        network = str(payload["network"])
        external_id = str(payload["external_post_id"])
        document_id = f"{network}:{external_id}"
        reference = self.client.collection("social_posts").document(document_id)
        await reference.set(payload, merge=True)
        return cast(str, reference.path)


async def queue_social_import(
    session: AsyncSession,
    *,
    principal: Principal,
    posts: list[SocialPostInput],
) -> int:
    assert principal.brand_id is not None
    now = clock.now()
    async with session.begin():
        validated: set[uuid.UUID] = set()
        for post in posts:
            if post.program_id not in validated:
                await get_program_for_brand(session, post.program_id, principal.brand_id)
                validated.add(post.program_id)
            if post.campaign_id:
                campaign_exists = await session.scalar(
                    select(Campaign.id).where(
                        Campaign.id == post.campaign_id,
                        Campaign.program_id == post.program_id,
                    )
                )
                if campaign_exists is None:
                    raise NotFoundError(
                        "campaign_not_found", "A post references a campaign outside its program"
                    )
            event_id = uuid.uuid5(
                uuid.NAMESPACE_URL, f"{post.network.value}:{post.external_post_id}"
            )
            payload = post.model_dump(mode="json")
            payload["brand_id"] = str(principal.brand_id)
            enqueue_event(
                session,
                aggregate_type="social_post",
                aggregate_id=event_id,
                event_type="social.post.detected",
                payload=payload,
                now=now,
            )
    return len(posts)


async def ingest_social_post(
    session: AsyncSession,
    *,
    payload: dict[str, Any],
    store: FirestoreListeningStore,
) -> ContentEvidence:
    post = SocialPostInput.model_validate(payload)
    firestore_path = await store.upsert(payload)
    brand_id = uuid.UUID(str(payload["brand_id"]))
    program_id = post.program_id
    campaign_id = post.campaign_id
    network = post.network
    handle = normalize_handle(post.handle)
    membership_id = await session.scalar(
        select(ProgramMembership.id)
        .join(SocialProfile, SocialProfile.creator_id == ProgramMembership.creator_id)
        .join(Program, Program.id == ProgramMembership.program_id)
        .where(
            ProgramMembership.program_id == program_id,
            ProgramMembership.status == MembershipStatus.ACTIVE,
            SocialProfile.network == network,
            SocialProfile.handle_normalized == handle,
            SocialProfile.verified.is_(True),
            Program.brand_id == brand_id,
        )
    )
    content_id = uuid.uuid4()
    statement = (
        pg_insert(ContentEvidence)
        .values(
            id=content_id,
            brand_id=brand_id,
            program_id=program_id,
            campaign_id=campaign_id,
            membership_id=membership_id,
            network=network,
            external_post_id=post.external_post_id,
            firestore_path=firestore_path,
            handle_normalized=handle,
            status=ContentStatus.MATCHED if membership_id else ContentStatus.DETECTED,
            published_at=post.published_at,
            metrics=post.metrics,
        )
        .on_conflict_do_update(
            constraint="uq_content_network_external",
            set_={
                "firestore_path": firestore_path,
                "metrics": post.metrics,
                "membership_id": membership_id,
                "status": ContentStatus.MATCHED if membership_id else ContentStatus.DETECTED,
            },
        )
        .returning(ContentEvidence.id)
    )
    persisted_id = (await session.execute(statement)).scalar_one()
    content = await session.get(ContentEvidence, persisted_id)
    assert content is not None
    return content


async def review_content(
    session: AsyncSession,
    *,
    principal: Principal,
    content_id: uuid.UUID,
    decision: ContentStatus,
) -> ContentEvidence:
    assert principal.brand_id is not None
    async with session.begin():
        content = await session.scalar(
            select(ContentEvidence)
            .where(
                ContentEvidence.id == content_id,
                ContentEvidence.brand_id == principal.brand_id,
            )
            .with_for_update()
        )
        if content is None:
            raise NotFoundError("content_not_found", "Content evidence was not found")
        content.status = decision
        content.reviewed_by = principal.user_id
        content.reviewed_at = clock.now()
    return content


async def list_content(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    status: ContentStatus | None = None,
) -> list[ContentEvidence]:
    statement = select(ContentEvidence).where(ContentEvidence.brand_id == brand_id)
    if status:
        statement = statement.where(ContentEvidence.status == status)
    return list(
        (await session.scalars(statement.order_by(ContentEvidence.published_at.desc()))).all()
    )
