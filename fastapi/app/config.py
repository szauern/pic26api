from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    token_cache_ttl: int = 300
    translation_cache_ttl: int = 3600
    rate_limit_window_seconds: int = 60
    debug: bool = False
    model_config = {"env_file": ".env"}

settings = Settings()
