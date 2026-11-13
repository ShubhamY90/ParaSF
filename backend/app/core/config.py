from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./paratrust.db"
    secret_key: str = "change-me-in-dev-only"
    access_token_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:5173"]
    simulation_seed: int = 42


settings = Settings()
