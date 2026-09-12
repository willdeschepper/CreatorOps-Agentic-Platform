import uuid
from typing import Any, cast

from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore
from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.config import settings
from creatorops.core.errors import ConflictError, NotFoundError
from creatorops.core.security import Principal
from creatorops.core.time import clock
from creatorops.models.enums import ContentStatus, MembershipStatus
from creatorops.models.identity import SocialProfile
from creatorops.models.listening import ContentEvidence
from creatorops.models.partnerships import ProgramMembership
from creatorops.models.programs import Campaign, Program
from creatorops.schemas import SocialPostInput
from creatorops.services.programs import get_program_for_brand
from creatorops.services.shared import add_audit, enqueue_event, normalize_handle


class FirestoreListeningStore:
    def __init__(self) -> None:
        if settings.app_env == "local" and not settings.firestore_emulator_host:
            raise RuntimeError("Local mode refuses to start without Firestore Emulator")
        self.client = firestore.AsyncClient(
            project=settings.local_project_id,
            credentials=AnonymousCredentials(),  # type: ignore[no-untyped-call]
        )

    async def upsert(self, payload: dict[str, object]) -> str:
        brand_id = str(payload["brand_id"])
        network = str(payload["network"])
        external_id = str(payload["external_post_id"])
        document_id = f"{brand_id}:{network}:{external_id}"
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
        known_posts: set[tuple[str, str]] = set()
        for post in posts:
            identity = (post.network.value, post.external_post_id)
            if identity in known_posts:
                raise ConflictError(
                    "duplicate_post_in_import", "The same post appears twice in this import"
                )
            known_posts.add(identity)
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
            existing = await session.scalar(
                select(ContentEvidence).where(
                    ContentEvidence.brand_id == principal.brand_id,
                    ContentEvidence.network == post.network,
                    ContentEvidence.external_post_id == post.external_post_id,
                )
            )
            if existing is not None and existing.status in {
                ContentStatus.APPROVED,
                ContentStatus.REJECTED,
            }:
                if any(
                    (
                        existing.program_id != post.program_id,
                        existing.campaign_id != post.campaign_id,
                        existing.handle_normalized != normalize_handle(post.handle),
                        existing.published_at != post.published_at,
                    )
                ):
                    raise ConflictError(
                        "reviewed_content_scope_conflict",
                        "Reviewed content scope can only change through an explicit human workflow",
                    )
            event_id = uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{principal.brand_id}:{post.network.value}:{post.external_post_id}",
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
    brand_id = uuid.UUID(str(payload["brand_id"]))
    program_id = post.program_id
    campaign_id = post.campaign_id
    network = post.network
    handle = normalize_handle(post.handle)
    existing = await session.scalar(
        select(ContentEvidence)
        .where(
            ContentEvidence.brand_id == brand_id,
            ContentEvidence.network == network,
            ContentEvidence.external_post_id == post.external_post_id,
        )
        .with_for_update()
    )
    reviewed_states = {ContentStatus.APPROVED, ContentStatus.REJECTED}
    if existing is not None and existing.status in reviewed_states:
        immutable_scope_changed = any(
            (
                existing.program_id != program_id,
                existing.campaign_id != campaign_id,
                existing.handle_normalized != handle,
                existing.published_at != post.published_at,
            )
        )
        if immutable_scope_changed:
            raise ConflictError(
                "reviewed_content_scope_conflict",
                "Reviewed content scope can only change through an explicit human workflow",
            )
    firestore_path = await store.upsert(payload)
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
            constraint="uq_content_brand_network_external",
            set_={
                "firestore_path": firestore_path,
                "metrics": post.metrics,
                "program_id": case(
                    (ContentEvidence.status.in_(reviewed_states), ContentEvidence.program_id),
                    else_=program_id,
                ),
                "campaign_id": case(
                    (ContentEvidence.status.in_(reviewed_states), ContentEvidence.campaign_id),
                    else_=campaign_id,
                ),
                "handle_normalized": case(
                    (
                        ContentEvidence.status.in_(reviewed_states),
                        ContentEvidence.handle_normalized,
                    ),
                    else_=handle,
                ),
                "published_at": case(
                    (ContentEvidence.status.in_(reviewed_states), ContentEvidence.published_at),
                    else_=post.published_at,
                ),
                "membership_id": case(
                    (ContentEvidence.status.in_(reviewed_states), ContentEvidence.membership_id),
                    else_=membership_id,
                ),
                "status": case(
                    (ContentEvidence.status.in_(reviewed_states), ContentEvidence.status),
                    else_=ContentStatus.MATCHED if membership_id else ContentStatus.DETECTED,
                ),
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
        previous = content.status
        content.status = decision
        content.reviewed_by = principal.user_id
        content.reviewed_at = clock.now()
        add_audit(
            session,
            brand_id=principal.brand_id,
            actor_user_id=principal.user_id,
            action="content.reviewed",
            entity_type="content_evidence",
            entity_id=content.id,
            data={"from": previous.value, "to": decision.value},
            now=content.reviewed_at,
        )
    return content


async def list_content(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    status: ContentStatus | None = None,
    program_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    membership_id: uuid.UUID | None = None,
    limit: int = 25,
    offset: int = 0,
) -> tuple[list[ContentEvidence], int]:
    statement = select(ContentEvidence).where(ContentEvidence.brand_id == brand_id)
    filters = [ContentEvidence.brand_id == brand_id]
    if status:
        filters.append(ContentEvidence.status == status)
    if program_id:
        filters.append(ContentEvidence.program_id == program_id)
    if campaign_id:
        filters.append(ContentEvidence.campaign_id == campaign_id)
    if membership_id:
        filters.append(ContentEvidence.membership_id == membership_id)
    total = int(
        await session.scalar(select(func.count()).select_from(ContentEvidence).where(*filters)) or 0
    )
    rows = list(
        (
            await session.scalars(
                statement.where(*filters)
                .order_by(ContentEvidence.published_at.desc(), ContentEvidence.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def get_content(
    session: AsyncSession, *, brand_id: uuid.UUID, content_id: uuid.UUID
) -> ContentEvidence:
    content = await session.scalar(
        select(ContentEvidence).where(
            ContentEvidence.id == content_id, ContentEvidence.brand_id == brand_id
        )
    )
    if content is None:
        raise NotFoundError("content_not_found", "Content evidence was not found")
    return content
