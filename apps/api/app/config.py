from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BENJI_", env_file=".env")

    database_url: str = "sqlite+aiosqlite:///./benji.db"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Delivery worker. Delays are seconds so a demo fails over in under a minute;
    # production values would be minutes to hours.
    retry_base_seconds: float = 2.0
    retry_cap_seconds: float = 30.0
    max_attempts: int = 5
    lease_seconds: float = 30.0
    http_timeout_seconds: float = 10.0
    worker_poll_seconds: float = 0.5
    worker_batch_size: int = 10
    worker_concurrency: int = 10

    # Signature verification tolerance on the receiving side (mock receivers, verify()).
    signature_tolerance_seconds: int = 300


settings = Settings()
