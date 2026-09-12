.PHONY: install up down logs migrate seed verify test lint typecheck demo reset

TEST_DATABASE_URL ?= postgresql+asyncpg://creatorops:creatorops@localhost:5434/creatorops_test

install:
	uv sync

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api worker provider-sim

migrate:
	uv run alembic upgrade head

seed:
	uv run creatorops-seed

lint:
	uv run ruff format --check .
	uv run ruff check .

typecheck:
	uv run mypy

test:
	docker compose --profile test up -d --wait test-db
	DATABASE_URL=$(TEST_DATABASE_URL) OTEL_ENABLED=false uv run alembic upgrade head
	DATABASE_URL=$(TEST_DATABASE_URL) OTEL_ENABLED=false uv run pytest --cov=creatorops --cov-report=term-missing

verify: lint typecheck test
	DATABASE_URL=$(TEST_DATABASE_URL) OTEL_ENABLED=false uv run alembic check

demo:
	uv run creatorops-demo

reset:
	docker compose down -v
