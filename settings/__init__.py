import os
from datetime import timedelta


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DB_URI = os.getenv(
    "DB_URI",
    "mysql+aiomysql://root:password@127.0.0.1:3306/ainame?charset=utf8mb4",
)
POSTGRES_MEMORY_URI = os.getenv(
    "POSTGRES_MEMORY_URI",
    "postgresql://postgres:password@127.0.0.1:5432/ainame",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your_deepseek_api_key")

MAIL_USERNAME = os.getenv("MAIL_USERNAME", "your_email@example.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "your_email_authorization_code")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME)
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.example.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "ainameapp")
MAIL_STARTTLS = _bool_env("MAIL_STARTTLS", True)
MAIL_SSL_TLS = _bool_env("MAIL_SSL_TLS", False)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(
    minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "15"))
)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(
    days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30"))
)
