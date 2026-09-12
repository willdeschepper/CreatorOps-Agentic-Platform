import asyncio
import contextlib
import signal

import structlog

from creatorops.core.config import settings
from creatorops.core.observability import configure_logging
from creatorops.services.commissions import settle_due_commissions
from creatorops.services.events import (
    dispatch_outbox_once,
    subscriber_client,
    subscription_callback,
)

logger = structlog.get_logger(__name__)


async def worker_loop() -> None:
    subscriber = subscriber_client()
    subscription_path = subscriber.subscription_path(
        settings.local_project_id, settings.pubsub_subscription
    )
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    streaming_future = subscriber.subscribe(subscription_path, callback=subscription_callback(loop))
    for signame in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(signame, stop.set)
    logger.info("worker_started", subscription=subscription_path)
    try:
        while not stop.is_set():
            try:
                await dispatch_outbox_once()
                # Settlement is idempotent and uses row-level skip-locked claims.
                from creatorops.core.db import session_factory

                async with session_factory() as session:
                    await settle_due_commissions(session)
            except Exception:
                logger.exception("worker_iteration_failed")
            try:
                await asyncio.wait_for(stop.wait(), timeout=settings.worker_poll_seconds)
            except TimeoutError:
                pass
    finally:
        streaming_future.cancel()
        subscriber.close()
        logger.info("worker_stopped")


def run() -> None:
    configure_logging()
    asyncio.run(worker_loop())


if __name__ == "__main__":
    run()
