import logging
import sys
import time
import uuid
from typing import Any

import structlog
from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram
from structlog.contextvars import bind_contextvars, clear_contextvars

from creatorops.core.config import settings
from creatorops.core.db import engine

REQUEST_COUNT = Counter(
    "creatorops_http_requests_total",
    "HTTP requests handled by CreatorOps",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "creatorops_http_request_duration_seconds",
    "CreatorOps HTTP request latency",
    ["method", "path"],
)


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(stream=sys.stdout, level=level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )


def configure_tracing(app: FastAPI) -> None:
    if not settings.otel_enabled:
        return
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "creatorops-api",
                "deployment.environment": settings.app_env,
            }
        )
    )
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


def install_http_observability(app: FastAPI) -> None:
    logger = structlog.get_logger("creatorops.http")

    @app.middleware("http")
    async def observe_request(request: Request, call_next: Any) -> Response:
        clear_contextvars()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        bind_contextvars(request_id=request_id)
        started = time.perf_counter()
        response: Response
        try:
            response = await call_next(request)
        except Exception:
            elapsed = time.perf_counter() - started
            REQUEST_COUNT.labels(request.method, request.url.path, "500").inc()
            REQUEST_LATENCY.labels(request.method, request.url.path).observe(elapsed)
            logger.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round(elapsed * 1000, 2),
            )
            raise
        elapsed = time.perf_counter() - started
        response.headers["X-Request-ID"] = request_id
        REQUEST_COUNT.labels(request.method, request.url.path, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(elapsed)
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(elapsed * 1000, 2),
        )
        clear_contextvars()
        return response
