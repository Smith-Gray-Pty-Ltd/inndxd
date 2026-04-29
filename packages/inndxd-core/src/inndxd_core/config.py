# packages/inndxd-core/src/inndxd_core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "INNDXD_", "env_file": ".env"}

    database_url: str = "postgresql+asyncpg://inndxd:inndxd@localhost:5432/inndxd"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "deepseek-r1:latest"
    log_level: str = "INFO"


settings = Settings()
