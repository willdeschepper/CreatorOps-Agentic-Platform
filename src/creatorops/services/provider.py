import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

import httpx

from creatorops.core.config import settings
from creatorops.models.enums import ProviderScenario


@dataclass(frozen=True, slots=True)
class ProviderTransfer:
    provider_reference: str
    idempotency_key: str
    payout_id: uuid.UUID
    beneficiary_id: uuid.UUID
    amount: Decimal
    currency: str
    status: str


class PayoutProvider(Protocol):
    async def create_transfer(
        self,
        *,
        payout_id: uuid.UUID,
        beneficiary_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        scenario: ProviderScenario,
    ) -> ProviderTransfer: ...

    async def find_by_key(self, idempotency_key: str) -> ProviderTransfer | None: ...

    async def statement(self, payout_id: uuid.UUID) -> list[ProviderTransfer]: ...


def _transfer(payload: dict[str, object]) -> ProviderTransfer:
    return ProviderTransfer(
        provider_reference=str(payload["provider_reference"]),
        idempotency_key=str(payload["idempotency_key"]),
        payout_id=uuid.UUID(str(payload["payout_id"])),
        beneficiary_id=uuid.UUID(str(payload["beneficiary_id"])),
        amount=Decimal(str(payload["amount"])),
        currency=str(payload["currency"]),
        status=str(payload["status"]),
    )


class LocalHttpPayoutProvider:
    def __init__(self, base_url: str | None = None, timeout: float | None = None) -> None:
        self.base_url = (base_url or settings.provider_base_url).rstrip("/")
        self.timeout = timeout or settings.provider_timeout_seconds

    async def create_transfer(
        self,
        *,
        payout_id: uuid.UUID,
        beneficiary_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        scenario: ProviderScenario,
    ) -> ProviderTransfer:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/transfers",
                headers={"Idempotency-Key": idempotency_key},
                json={
                    "payout_id": str(payout_id),
                    "beneficiary_id": str(beneficiary_id),
                    "amount": str(amount),
                    "currency": currency,
                    "scenario": scenario.value,
                },
            )
            response.raise_for_status()
            return _transfer(response.json())

    async def find_by_key(self, idempotency_key: str) -> ProviderTransfer | None:
        async with httpx.AsyncClient(timeout=max(self.timeout, 2.0)) as client:
            response = await client.get(f"{self.base_url}/transfers/by-key/{idempotency_key}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return _transfer(response.json())

    async def statement(self, payout_id: uuid.UUID) -> list[ProviderTransfer]:
        async with httpx.AsyncClient(timeout=max(self.timeout, 2.0)) as client:
            response = await client.get(
                f"{self.base_url}/statement", params={"payout_id": str(payout_id)}
            )
            response.raise_for_status()
            return [_transfer(item) for item in response.json()]


provider: PayoutProvider = LocalHttpPayoutProvider()
