"""Application configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "support-ticket-api"
    debug: bool = False
    secret_key: str = "change-me-in-production-use-env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "postgresql://postgres:postgres@postgres:5432/tickets"
    otlp_endpoint: str = "http://otel-collector:4317"
    loki_url: str = "http://loki:3100/loki/api/v1/push"
    # Observability demo: set via env to enable (e.g. ENABLE_ANOMALY_DELAY=true, ANOMALY_ERROR_RATE=0.1)
    enable_anomaly_delay: bool = False
    anomaly_delay_seconds: float = 0.5
    anomaly_error_rate: float = 0.0
    enable_slow_query_simulation: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
