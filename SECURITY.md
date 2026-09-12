# Security policy

## Local-only prototype

CreatorOps is an educational, local-first prototype. It must not be used with real customer,
creator, commerce, social-network or banking data.

The credentials and secrets present in `.env.example`, Docker Compose, the README and Bruno
are intentionally public development defaults. They are accepted only when `APP_ENV=local`
and must never be reused in another environment.

## Before publishing or sharing changes

- Keep `.env`, private keys, database files, logs and `docs/private/` out of Git.
- Use only synthetic fixtures and `@creatorops.dev` identities.
- Do not commit exports from Postgres, Firestore, Jaeger or the provider simulator.
- Run `make verify` and inspect `git status --ignored` before pushing.
- Rotate any credential immediately if real data is committed, even if the commit is later
  removed.

Security issues in this portfolio project should be reported privately to the repository
owner rather than through a public issue.
