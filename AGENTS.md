# CreatorOps engineering contract

This repository is a local-first backend exercise. Agents may implement scoped work, but a
human owns every accepted diff.

## Non-negotiable invariants

- Never represent money with `float`; use `Decimal` and PostgreSQL `NUMERIC`.
- Never mutate or delete financial ledger rows; correct them with compensating entries.
- Never use `Base.metadata.create_all`; schema changes require Alembic migrations.
- Never commit inside repositories. Application services own transaction boundaries.
- Every tenant-owned query must include the active brand explicitly.
- Webhook, inbox, outbox, payout, and proposal execution paths must be idempotent.
- A payout in `unknown` must never be retried with a new idempotency key.
- An agent proposal may not execute without fresh gates and recorded human approval.
- Local mode must require emulator hosts and must never fall back to real GCP endpoints.
- Domain services raise domain errors, not FastAPI `HTTPException`.

## Required gates

Run `make verify` before accepting a change. Review migrations, transaction boundaries,
tenant filters, state transitions, and tests in every domain-affecting diff.
