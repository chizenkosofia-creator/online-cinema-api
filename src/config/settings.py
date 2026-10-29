from pydantic import EmailStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    redis_url: str = "redis://redis:6379/0"
    REDIS_URL: str = "redis://redis:6379/0"

    DATABASE_URL: str
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/online_cinema"

    @computed_field
    @property
    def computed_redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7
    ACTIVATION_TOKEN_HOURS: int = 24
    PASSWORD_RESET_TOKEN_HOURS: int = 1

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025
    EMAIL_FROM: EmailStr = "no-reply@cinema.com"
    FRONTEND_URL: str = "http://localhost:3000"

    DOCS_USERNAME: str
    DOCS_PASSWORD: str

    # Mail settings for fastapi-mail (optional for Mailhog)
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str = "no-reply@cinema.com"
    MAIL_PORT: int = 1025
    MAIL_SERVER: str = "mailhog"
    MAIL_FROM_NAME: str = "Online Cinema"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
