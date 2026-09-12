import asyncio
import json
import os
import uuid
from collections.abc import Callable
from typing import Any

import structlog
from google.auth.credentials import AnonymousCredentials
from google.cloud import pubsub_v1  # type: ignore[attr-defined]
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.config import settings
from creatorops.core.db import session_factory
from creatorops.core.time import clock
from creatorops.models.events import InboxMessage, OutboxEvent
from creatorops.services.finance import process_payout
from creatorops.services.listening import FirestoreListeningStore, ingest_social_post

logger = structlog.get_logger(__name__)


def configure_emulator_environment() -> None:
    if settings.app_env == "local":
        if not settings.pubsub_emulator_host or not settings.firestore_emulator_host:
            raise RuntimeError("Local mode refuses to use real GCP endpoints")
        os.environ["PUBSUB_EMULATOR_HOST"] = settings.pubsub_emulator_host
        os.environ["FIRESTORE_EMULATOR_HOST"] = settings.firestore_emulator_host


def publisher_client() -> pubsub_v1.PublisherClient:
    configure_emulator_environment()
    return pubsub_v1.PublisherClient(
        credentials=AnonymousCredentials()  # type: ignore[no-untyped-call]
    )


def subscriber_client() -> pubsub_v1.SubscriberClient:
    configure_emulator_environment()
    return pubsub_v1.SubscriberClient(
        credentials=AnonymousCredentials()  # type: ignore[no-untyped-call]
    )


async def dispatch_outbox_once(limit: int = 100) -> int:
    publisher = publisher_client()
    topic_path = publisher.topic_path(settings.local_project_id, settings.pubsub_topic)
    published = 0
    async with session_factory() as session, session.begin():
        events = list(
            (
                await session.scalars(
                    select(OutboxEvent)
                    .where(OutboxEvent.published_at.is_(None))
                    .order_by(OutboxEvent.created_at)
                    .limit(limit)
                    .with_for_update(skip_locked=True)
                )
            ).all()
        )
        for event in events:
            envelope = {
                "id": str(event.id),
                "event_type": event.event_type,
                "occurred_at": event.created_at.isoformat(),
                "payload": event.payload,
            }
            try:
                future = publisher.publish(
                    topic_path,
                    json.dumps(envelope, separators=(",", ":")).encode(),
                    event_type=event.event_type,
                )
                await asyncio.to_thread(future.result, timeout=5)
                event.published_at = clock.now()
                event.attempts += 1
                event.last_error = None
                published += 1
            except Exception as exc:
                event.attempts += 1
                event.last_error = str(exc)[:1000]
                logger.exception("outbox_publish_failed", event_id=str(event.id))
    return published


async def _inbox_seen(session: AsyncSession, message_id: str) -> bool:
    return (
        await session.scalar(
            select(InboxMessage.id).where(
                InboxMessage.consumer == "creatorops-worker",
                InboxMessage.message_id == message_id,
            )
        )
        is not None
    )


async def handle_envelope(envelope: dict[str, Any]) -> None:
    message_id = str(envelope["id"])
    event_type = str(envelope["event_type"])
    payload = dict(envelope.get("payload") or {})
    async with session_factory() as check_session:
        if await _inbox_seen(check_session, message_id):
            return

    if event_type == "payout.requested":
        await process_payout(uuid.UUID(str(payload["payout_id"])))
    elif event_type == "social.post.detected":
        async with session_factory() as session, session.begin():
            await ingest_social_post(
                session,
                payload=payload,
                store=FirestoreListeningStore(),
            )

    async with session_factory() as session, session.begin():
        await session.execute(
            pg_insert(InboxMessage)
            .values(
                consumer="creatorops-worker",
                message_id=message_id,
                event_type=event_type,
                processed_at=clock.now(),
            )
            .on_conflict_do_nothing(index_elements=["consumer", "message_id"])
        )


def subscription_callback(loop: asyncio.AbstractEventLoop) -> Callable[[Any], None]:
    def callback(message: Any) -> None:
        try:
            envelope = json.loads(message.data.decode())
            future = asyncio.run_coroutine_threadsafe(handle_envelope(envelope), loop)
            future.result(timeout=30)
        except Exception:
            logger.exception("pubsub_message_failed", pubsub_message_id=message.message_id)
            message.nack()
        else:
            message.ack()

    return callback
