import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./paratrust.db"
    secret_key: str = "change-me-in-dev-only"
    access_token_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:5173"]
    simulation_seed: int = 42


settings = Settings()

if settings.secret_key == "change-me-in-dev-only":
    logger.warning(
        "⚠️  ParaTrust: SECRET_KEY is set to the default dev value. "
        "Set SECRET_KEY in backend/.env before deploying."
    )
