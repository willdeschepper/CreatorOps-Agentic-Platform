FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src
COPY provider_sim ./provider_sim
COPY fixtures ./fixtures
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uvicorn", "creatorops.main:app", "--host", "0.0.0.0", "--port", "8000"]
