from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./taskflow_demo.db"
    jwt_secret: str = "dev-only-change-me"
    webhook_secret: str = "demo-webhook-secret"
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

    class Config:
        env_prefix = ""
        env_file = ".env"
        extra = "ignore"


settings = Settings()
