import os
import time

from google.api_core.exceptions import AlreadyExists
from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore, pubsub_v1  # type: ignore[attr-defined]

from creatorops.core.config import settings


def initialize() -> None:
    if settings.app_env != "local":
        raise RuntimeError("Emulator initialization is local-only")
    if not settings.pubsub_emulator_host or not settings.firestore_emulator_host:
        raise RuntimeError("Both GCP emulator hosts are required")
    os.environ["PUBSUB_EMULATOR_HOST"] = settings.pubsub_emulator_host
    os.environ["FIRESTORE_EMULATOR_HOST"] = settings.firestore_emulator_host

    last_error: Exception | None = None
    for _ in range(45):
        try:
            publisher = pubsub_v1.PublisherClient(
                credentials=AnonymousCredentials()  # type: ignore[no-untyped-call]
            )
            subscriber = pubsub_v1.SubscriberClient(
                credentials=AnonymousCredentials()  # type: ignore[no-untyped-call]
            )
            topic_path = publisher.topic_path(settings.local_project_id, settings.pubsub_topic)
            subscription_path = subscriber.subscription_path(
                settings.local_project_id, settings.pubsub_subscription
            )
            try:
                publisher.create_topic(request={"name": topic_path})
            except AlreadyExists:
                pass
            try:
                subscriber.create_subscription(
                    request={"name": subscription_path, "topic": topic_path}
                )
            except AlreadyExists:
                pass
            client = firestore.Client(
                project=settings.local_project_id,
                credentials=AnonymousCredentials(),  # type: ignore[no-untyped-call]
            )
            client.collection("_system").document("ready").set({"ready": True})
            return
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Local emulators did not become ready: {last_error}")


def run() -> None:
    initialize()


if __name__ == "__main__":
    run()
