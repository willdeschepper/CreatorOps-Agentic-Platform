from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CreatorOps Agentic Platform"
    app_env: str = "local"
    api_prefix: str = "/v1"
    database_url: str = "postgresql+asyncpg://creatorops:creatorops@localhost:5433/creatorops"

    jwt_secret: str = Field(default="local-jwt-secret-change-me", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    commerce_webhook_secret: str = Field(default="local-commerce-secret", min_length=12)

    local_project_id: str = "creatorops-local"
    pubsub_emulator_host: str | None = "localhost:8085"
    firestore_emulator_host: str | None = "localhost:8080"
    pubsub_topic: str = "creatorops-events"
    pubsub_subscription: str = "creatorops-worker"
    emulator_required: bool = True

    provider_base_url: str = "http://localhost:8090"
    provider_timeout_seconds: float = 0.75

    otel_enabled: bool = True
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    log_level: str = "INFO"

    worker_poll_seconds: float = 1.0
    reconciliation_unknown_after_seconds: int = 30

    @model_validator(mode="after")
    def prevent_real_cloud_fallback(self) -> "Settings":
        if self.app_env == "local" and self.emulator_required:
            if not self.pubsub_emulator_host or not self.firestore_emulator_host:
                raise ValueError(
                    "local mode requires PUBSUB_EMULATOR_HOST and FIRESTORE_EMULATOR_HOST"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
