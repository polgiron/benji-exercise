from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BENJI_", env_file=".env")

    database_url: str = "sqlite+aiosqlite:///./benji.db"
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
