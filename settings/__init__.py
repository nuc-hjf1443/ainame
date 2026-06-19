from datetime import timedelta
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DB_URI: str = "mysql+aiomysql://root:password@127.0.0.1:3306/ainame?charset=utf8mb4"
    POSTGRES_MEMORY_URI: str = "postgresql://postgres:password@127.0.0.1:5432/ainame"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    DEEPSEEK_API_KEY: str = "your_deepseek_api_key"

    MAIL_USERNAME: str = "your_email@example.com"
    MAIL_PASSWORD: str = "your_email_authorization_code"
    MAIL_FROM: str | None = None
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_FROM_NAME: str = "ainameapp"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    JWT_SECRET_KEY: str = "change-this-secret"
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRES_DAYS: int = 30


_settings = AppSettings()

DB_URI = _settings.DB_URI
POSTGRES_MEMORY_URI = _settings.POSTGRES_MEMORY_URI
REDIS_URL = _settings.REDIS_URL

DEEPSEEK_API_KEY = _settings.DEEPSEEK_API_KEY

MAIL_USERNAME = _settings.MAIL_USERNAME
MAIL_PASSWORD = _settings.MAIL_PASSWORD
MAIL_FROM = _settings.MAIL_FROM or _settings.MAIL_USERNAME
MAIL_PORT = _settings.MAIL_PORT
MAIL_SERVER = _settings.MAIL_SERVER
MAIL_FROM_NAME = _settings.MAIL_FROM_NAME
MAIL_STARTTLS = _settings.MAIL_STARTTLS
MAIL_SSL_TLS = _settings.MAIL_SSL_TLS

JWT_SECRET_KEY = _settings.JWT_SECRET_KEY
JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=_settings.JWT_ACCESS_TOKEN_EXPIRES_MINUTES)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=_settings.JWT_REFRESH_TOKEN_EXPIRES_DAYS)
