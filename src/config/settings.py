from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
