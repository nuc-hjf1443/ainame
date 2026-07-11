from datetime import timedelta
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent if BACKEND_DIR.name == "ainamebackend" else BACKEND_DIR
BASE_DIR = BACKEND_DIR


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env", PROJECT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DB_URI: str = "mysql+aiomysql://root:password@127.0.0.1:3306/ainame?charset=utf8mb4"
    POSTGRES_MEMORY_URI: str = "postgresql://postgres:password@127.0.0.1:5432/ainame"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    RABBITMQ_URL: str = "amqp://127.0.0.1:5672/"
    RAG_QUEUE_NAME: str = "rag_document_queue"
    ENABLE_MOCK_PAYMENT: bool = False
    ALIPAY_ENABLED: bool = False
    ALIPAY_GATEWAY_URL: str = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
    ALIPAY_APP_ID: str = ""
    ALIPAY_APP_PRIVATE_KEY_PATH: str = ""
    ALIPAY_PUBLIC_KEY_PATH: str = ""
    ALIPAY_NOTIFY_URL: str = ""
    ALIPAY_RETURN_URL: str = ""
    FRONTEND_BASE_URL: str = "http://127.0.0.1:5173"
    ALIPAY_SIGN_TYPE: str = "RSA2"
    ALIPAY_PAY_METHOD: str = "page"

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

    AIGC_API_BASE_URL: str = ""
    AIGC_API_KEY: str = ""
    AIGC_SUBMIT_PATH: str = "/submit"
    AIGC_FETCH_PATH_TEMPLATE: str = "/task/{task_id}"
    AIGC_TIMEOUT_SECONDS: int = 10
    AIGC_WAN_IMAGE_URL: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    AIGC_IMAGE_SYNTHESIS_URL: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    AIGC_TASK_URL_TEMPLATE: str = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    AIGC_GENERATION_TIMEOUT_SECONDS: int = 180
    AIGC_NETWORK_RETRY_ATTEMPTS: int = 3
    PUBLIC_BASE_URL: str = "http://127.0.0.1:8000"
    VISUAL_MAX_FILE_SIZE: int = 10 * 1024 * 1024
    PDF_FONT_PATH: str = ""
    PDF_FONT_BOLD_PATH: str = ""


_settings = AppSettings()


def _resolve_path(value: str) -> str:
    if not value:
        return ""
    path = Path(value)
    if path.is_absolute():
        if path.exists():
            return str(path)
        try:
            relative_path = path.relative_to(PROJECT_DIR)
        except ValueError:
            return str(path)
        moved_path = BACKEND_DIR / relative_path
        if moved_path.exists():
            return str(moved_path)
        return str(path)
    for base_dir in (BACKEND_DIR, PROJECT_DIR):
        candidate = base_dir / path
        if candidate.exists():
            return str(candidate)
    return str(BACKEND_DIR / path)


DB_URI = _settings.DB_URI
POSTGRES_MEMORY_URI = _settings.POSTGRES_MEMORY_URI
REDIS_URL = _settings.REDIS_URL
RABBITMQ_URL = _settings.RABBITMQ_URL
RAG_QUEUE_NAME = _settings.RAG_QUEUE_NAME
ENABLE_MOCK_PAYMENT = _settings.ENABLE_MOCK_PAYMENT
ALIPAY_ENABLED = _settings.ALIPAY_ENABLED
ALIPAY_GATEWAY_URL = _settings.ALIPAY_GATEWAY_URL
ALIPAY_APP_ID = _settings.ALIPAY_APP_ID
ALIPAY_APP_PRIVATE_KEY_PATH = _resolve_path(_settings.ALIPAY_APP_PRIVATE_KEY_PATH)
ALIPAY_PUBLIC_KEY_PATH = _resolve_path(_settings.ALIPAY_PUBLIC_KEY_PATH)
ALIPAY_NOTIFY_URL = _settings.ALIPAY_NOTIFY_URL
ALIPAY_RETURN_URL = _settings.ALIPAY_RETURN_URL
FRONTEND_BASE_URL = _settings.FRONTEND_BASE_URL.rstrip("/")
ALIPAY_SIGN_TYPE = _settings.ALIPAY_SIGN_TYPE
ALIPAY_PAY_METHOD = _settings.ALIPAY_PAY_METHOD

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

AIGC_API_BASE_URL = _settings.AIGC_API_BASE_URL
AIGC_API_KEY = _settings.AIGC_API_KEY
AIGC_SUBMIT_PATH = _settings.AIGC_SUBMIT_PATH
AIGC_FETCH_PATH_TEMPLATE = _settings.AIGC_FETCH_PATH_TEMPLATE
AIGC_TIMEOUT_SECONDS = _settings.AIGC_TIMEOUT_SECONDS
AIGC_WAN_IMAGE_URL = _settings.AIGC_WAN_IMAGE_URL
AIGC_IMAGE_SYNTHESIS_URL = _settings.AIGC_IMAGE_SYNTHESIS_URL
AIGC_TASK_URL_TEMPLATE = _settings.AIGC_TASK_URL_TEMPLATE
AIGC_GENERATION_TIMEOUT_SECONDS = _settings.AIGC_GENERATION_TIMEOUT_SECONDS
AIGC_NETWORK_RETRY_ATTEMPTS = max(1, _settings.AIGC_NETWORK_RETRY_ATTEMPTS)
PUBLIC_BASE_URL = _settings.PUBLIC_BASE_URL.rstrip("/")
VISUAL_MAX_FILE_SIZE = _settings.VISUAL_MAX_FILE_SIZE
PDF_FONT_PATH = _resolve_path(_settings.PDF_FONT_PATH)
PDF_FONT_BOLD_PATH = _resolve_path(_settings.PDF_FONT_BOLD_PATH)
