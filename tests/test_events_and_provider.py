import uuid
from decimal import Decimal
from pathlib import Path

from httpx import ASGITransport, AsyncClient
from provider_sim import main as provider_app
from sqlalchemy import func, select

from creatorops.core.db import session_factory
from creatorops.models.events import InboxMessage
from creatorops.services.events import handle_envelope


async def test_inbox_deduplicates_repeated_pubsub_envelope() -> None:
    event_id = str(uuid.uuid4())
    envelope = {
        "id": event_id,
        "event_type": "test.noop",
        "payload": {"value": 1},
    }
    await handle_envelope(envelope)
    await handle_envelope(envelope)
    async with session_factory() as session:
        count = await session.scalar(
            select(func.count(InboxMessage.id)).where(InboxMessage.message_id == event_id)
        )
    assert count == 1


async def test_provider_simulator_preserves_idempotency(tmp_path: Path) -> None:
    path = tmp_path / "provider.db"
    provider_app.DB_PATH = str(path)
    transport = ASGITransport(app=provider_app.app)
    payload = {
        "payout_id": str(uuid.uuid4()),
        "beneficiary_id": str(uuid.uuid4()),
        "amount": "25.00",
        "currency": "BRL",
        "scenario": "success",
    }
    async with AsyncClient(transport=transport, base_url="http://provider") as client:
        first = await client.post(
            "/transfers", json=payload, headers={"Idempotency-Key": "same-key-123"}
        )
        replay = await client.post(
            "/transfers", json=payload, headers={"Idempotency-Key": "same-key-123"}
        )
        changed = await client.post(
            "/transfers",
            json=dict(payload, amount=str(Decimal("26.00"))),
            headers={"Idempotency-Key": "same-key-123"},
        )
    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json()["provider_reference"] == first.json()["provider_reference"]
    assert changed.status_code == 409
