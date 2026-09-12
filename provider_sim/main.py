import asyncio
import hashlib
import json
import os
import sqlite3
import threading
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

DB_PATH = os.getenv("PROVIDER_DB_PATH", "/tmp/creatorops-provider.db")
TIMEOUT_DELAY = float(os.getenv("PROVIDER_TIMEOUT_DELAY_SECONDS", "1.5"))
lock = threading.Lock()


def connection() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS transfers (
            id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            payout_id TEXT NOT NULL,
            beneficiary_id TEXT NOT NULL,
            amount TEXT NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    db.commit()
    return db


class TransferRequest(BaseModel):
    payout_id: uuid.UUID
    beneficiary_id: uuid.UUID
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: Literal["BRL"] = "BRL"
    scenario: Literal["success", "failure", "timeout_before", "timeout_after"] = "success"


class TransferResponse(BaseModel):
    provider_reference: str
    idempotency_key: str
    payout_id: uuid.UUID
    beneficiary_id: uuid.UUID
    amount: Decimal
    currency: str
    status: Literal["confirmed", "failed"]
    created_at: datetime


app = FastAPI(
    title="CreatorOps Local Payout Provider",
    version="0.1.0",
    description="A deliberately unreliable local provider used to exercise reconciliation.",
)


def row_to_response(row: sqlite3.Row) -> TransferResponse:
    return TransferResponse(
        provider_reference=row["id"],
        idempotency_key=row["idempotency_key"],
        payout_id=row["payout_id"],
        beneficiary_id=row["beneficiary_id"],
        amount=Decimal(row["amount"]),
        currency=row["currency"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/transfers", response_model=TransferResponse)
async def create_transfer(
    body: TransferRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=240),
) -> TransferResponse:
    payload = body.model_dump(mode="json", exclude={"scenario"})
    payload_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with lock, connection() as db:
        existing = db.execute(
            "SELECT * FROM transfers WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
        if existing:
            if existing["payload_hash"] != payload_hash:
                raise HTTPException(409, "idempotency key reused with different transfer")
            return row_to_response(existing)

    if body.scenario == "timeout_before":
        await asyncio.sleep(TIMEOUT_DELAY)
        raise HTTPException(504, "simulated timeout before processing")

    reference = f"tr_{uuid.uuid4().hex}"
    status = "failed" if body.scenario == "failure" else "confirmed"
    now = datetime.now(UTC)
    with lock, connection() as db:
        db.execute(
            """
            INSERT INTO transfers (
                id, idempotency_key, payout_id, beneficiary_id, amount,
                currency, status, payload_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reference,
                idempotency_key,
                str(body.payout_id),
                str(body.beneficiary_id),
                str(body.amount.quantize(Decimal("0.01"))),
                body.currency,
                status,
                payload_hash,
                now.isoformat(),
            ),
        )
        db.commit()
        row = db.execute("SELECT * FROM transfers WHERE id = ?", (reference,)).fetchone()
        assert row is not None
        response = row_to_response(row)

    if body.scenario == "timeout_after":
        await asyncio.sleep(TIMEOUT_DELAY)
    return response


@app.get("/transfers/by-key/{idempotency_key}", response_model=TransferResponse)
async def find_transfer(idempotency_key: str) -> TransferResponse:
    with lock, connection() as db:
        row = db.execute(
            "SELECT * FROM transfers WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
    if row is None:
        raise HTTPException(404, "transfer not found")
    return row_to_response(row)


@app.get("/statement", response_model=list[TransferResponse])
async def statement(payout_id: uuid.UUID | None = Query(default=None)) -> list[TransferResponse]:
    with lock, connection() as db:
        if payout_id:
            rows = db.execute(
                "SELECT * FROM transfers WHERE payout_id = ? ORDER BY created_at", (str(payout_id),)
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM transfers ORDER BY created_at").fetchall()
    return [row_to_response(row) for row in rows]
