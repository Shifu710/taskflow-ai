from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./taskflow_demo.db"
    jwt_secret: str = "dev-only-change-me"
    webhook_secret: str = "demo-webhook-secret"
    ai_provider: str = "demo-local"
    ai_api_key: str | None = None
    ai_model: str = "demo-local"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str | None = None

    class Config:
        env_prefix = ""
        env_file = ".env"
        extra = "ignore"


settings = Settings()
