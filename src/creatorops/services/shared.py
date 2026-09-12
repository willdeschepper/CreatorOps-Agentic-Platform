import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.models.events import AuditLog, OutboxEvent


def add_audit(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    data: dict[str, object],
    now: datetime,
) -> None:
    session.add(
        AuditLog(
            brand_id=brand_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
            created_at=now,
        )
    )


def enqueue_event(
    session: AsyncSession,
    *,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    event_type: str,
    payload: dict[str, object],
    now: datetime,
) -> OutboxEvent:
    event = OutboxEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        created_at=now,
    )
    session.add(event)
    return event


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_handle(value: str) -> str:
    return value.strip().lower().lstrip("@").replace(" ", "")
