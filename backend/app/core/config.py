from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me"

    DATABASE_URL: str = "postgresql+asyncpg://govscan:changeme@db:5432/govscan"

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    SCRAPER_MAX_WORKERS: int = 5
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 GovScan/1.0"
    )


settings = Settings()
