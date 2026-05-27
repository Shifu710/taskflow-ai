from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./taskflow_demo.db"
    redis_url: str = "redis://localhost:6379/0"
    taskflow_use_celery: bool = False
    jwt_secret: str = Field(
        default="dev-only-change-me",
        validation_alias=AliasChoices("TASKFLOW_JWT_SECRET", "JWT_SECRET"),
    )
    webhook_secret: str = Field(
        default="demo-webhook-secret",
        validation_alias=AliasChoices("TASKFLOW_WEBHOOK_SECRET", "WEBHOOK_SECRET"),
    )
    ai_provider: str = "demo-local"
    ai_api_key: str | None = None
    ai_model: str = "demo-local"
    deepseek_api_key: str | None = None
    deepseek_model: str = "deepseek-chat"
    qwen_api_key: str | None = None
    qwen_model: str = "qwen-plus"
    openai_compatible_api_key: str | None = None
    openai_compatible_base_url: str = "https://api.openai.com/v1"
    openai_compatible_model: str = "gpt-4o-mini"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str | None = None
    frontend_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://") and "+psycopg" not in value:
            value = value.replace("postgresql://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql") and "sslmode=" not in value:
            separator = "&" if "?" in value else "?"
            value = f"{value}{separator}sslmode=require"
        return value


settings = Settings()
