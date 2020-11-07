import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import (
    AnyHttpUrl,
    BaseSettings,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    RedisDsn,
    validator,
)


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes = 1 hour
    OTP_TOKEN_EXPIRE_MINUTES: int = 60
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SERVER_NAME: str
    SERVER_HOST: AnyHttpUrl
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str
    SENTRY_DSN: Optional[HttpUrl] = None

    @validator("SENTRY_DSN", pre=True)
    def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:
        if len(v) == 0:
            return None
        return v

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None

    @validator("EMAILS_FROM_NAME")
    def get_project_name(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if not v:
            return values["PROJECT_NAME"]
        return v

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "/app/app/email-templates/build"
    EMAILS_ENABLED: bool = False

    @validator("EMAILS_ENABLED", pre=True)
    def get_emails_enabled(cls, v: bool, values: Dict[str, Any]) -> bool:
        return bool(
            values.get("SMTP_HOST")
            and values.get("SMTP_PORT")
            and values.get("EMAILS_FROM_EMAIL")
        )

    EMAIL_TEST_USER: EmailStr = "test@example.com"  # type: ignore
    FIRST_SUPERUSER_USERNAME: str
    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_MOBILE: str
    FIRST_SUPERUSER_PASSWORD: str
    USERS_OPEN_REGISTRATION: bool = False

    LOG_LEVEL: str = "info"

    REDIS_HOST: str
    REDIS_PORT: Optional[str] = None
    REDIS_USER: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None
    APP_REDIS_DB: int
    CELERY_REDIS_DB: int
    PUSHER_REDIS_DB: int
    APP_REDIS_DSN: Optional[RedisDsn] = None
    CELERY_REDIS_DSN: Optional[RedisDsn] = None
    PUSHER_REDIS_DSN: Optional[RedisDsn] = None

    @validator("APP_REDIS_DSN", pre=True)
    def assemble_app_redis_connection(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT"),
            user=values.get("REDIS_USER"),
            password=values.get("REDIS_PASSWORD"),
            path=f"/{values.get('APP_REDIS_DB')}",
        )

    @validator("CELERY_REDIS_DSN", pre=True)
    def assemble_celery_redis_connection(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT"),
            user=values.get("REDIS_USER"),
            password=values.get("REDIS_PASSWORD"),
            path=f"/{values.get('CELERY_REDIS_DB')}",
        )

    @validator("PUSHER_REDIS_DSN", pre=True)
    def assemble_pusher_redis_connection(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT"),
            user=values.get("REDIS_USER"),
            password=values.get("REDIS_PASSWORD"),
            path=f"/{values.get('PUSHER_REDIS_DB')}",
        )

    ACCESS_TOKEN_URL: Optional[str] = None

    @validator("ACCESS_TOKEN_URL", pre=True)
    def set_access_token_url(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        return v or (values["API_V1_STR"] + "/login/access-token")

    PUSHER_USER_NAMESPACE: str = "/user"

    SMS_IS_ACTIVE: bool = False
    SMS_API_KEY: Optional[str] = None
    SMS_SECRET_KEY: Optional[str] = None
    SMS_OTP_DEFAULT_TEMPLATE_ID: Optional[int] = None

    SMS_REGISTRATION_TEMPLATE_ID: Optional[int] = None

    @validator("SMS_REGISTRATION_TEMPLATE_ID", pre=True)
    def set_registration_template_to_default_if_none(
        cls, v: Optional[int], values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, int):
            return v
        return values.get("SMS_OTP_DEFAULT_TEMPLATE_ID")

    SMS_LOGIN_TEMPLATE_ID: Optional[int] = None

    @validator("SMS_LOGIN_TEMPLATE_ID", pre=True)
    def set_login_template_to_default_if_none(
        cls, v: Optional[int], values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, int):
            return v
        return values.get("SMS_OTP_DEFAULT_TEMPLATE_ID")

    # Update SMS client token every hour = 60 minutes * 60 seconds
    SMS_UPDATE_TOKEN_INTERVAL: int = 60 * 60

    OTP_EXPIRE_SECONDS: int = 120
    REGISTRATION_EXPIRE_SECONDS: int = 60 * 60

    class Config:
        case_sensitive = True


settings = Settings()
