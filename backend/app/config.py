from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://postgres:test1234@localhost:5432/absence_engine"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 300
    db_pool_pre_ping: bool = True

    redis_url: str = "redis://localhost:6379/0"

    # Local filesystem storage (used in place of S3 during development)
    local_storage_dir: str = "./uploads"

    max_upload_bytes: int = 52_428_800

    jwt_secret_key: str = "dev-secret-change-in-production-use-64-char-random-string-here-xx"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    llm_primary_provider: str = "openai"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_fallback_chain: str = "gemini,anthropic"
    llm_max_retries: int = 3
    llm_circuit_breaker_threshold: int = 5
    llm_circuit_breaker_timeout: int = 60
    llm_max_tokens_per_analysis: int = 50000

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 768

    rate_limit_auth: str = "5/minute"
    rate_limit_upload: str = "10/minute"
    rate_limit_analysis: str = "5/minute"
    rate_limit_general: str = "60/minute"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
