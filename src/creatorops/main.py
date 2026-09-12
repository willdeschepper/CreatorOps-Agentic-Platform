import uvicorn
from fastapi import FastAPI

from creatorops.core.config import settings
from creatorops.core.errors import install_error_handlers
from creatorops.core.observability import (
    configure_logging,
    configure_tracing,
    install_http_observability,
)
from creatorops.routers import (
    agent,
    auth,
    commerce,
    commissions,
    finance,
    health,
    listening,
    partnerships,
    programs,
    reports,
)


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Local-first backend for influencer and affiliate operations, financial "
            "reconciliation, and deterministic agent-control workflows."
        ),
    )
    install_error_handlers(app)
    install_http_observability(app)
    app.include_router(health.router)
    app.include_router(commerce.redirect_router)
    for router in (
        auth.router,
        programs.router,
        partnerships.router,
        commerce.router,
        commissions.router,
        listening.router,
        finance.router,
        agent.router,
        reports.router,
    ):
        app.include_router(router, prefix=settings.api_prefix)
    configure_tracing(app)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("creatorops.main:app", host="0.0.0.0", port=8000, reload=False)
