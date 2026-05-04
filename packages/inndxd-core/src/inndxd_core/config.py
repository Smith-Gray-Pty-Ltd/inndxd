# packages/inndxd-core/src/inndxd_core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "INNDXD_", "env_file": ".env", "extra": "ignore"}

    database_url: str = "postgresql+asyncpg://inndxd:inndxd@localhost:5432/inndxd"
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    jwt_secret: str = "inndxd-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    llm_provider_name: str = "default"
    llm_provider_type: str = "openai_compatible"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "deepseek-r1:latest"

    ollama_base_url: str = ""
    ollama_model: str = ""

    def model_post_init(self, __context: object) -> None:
        if self.ollama_base_url and self.llm_base_url == "http://localhost:11434/v1":
            object.__setattr__(self, "llm_base_url", self.ollama_base_url)
        if self.ollama_model and self.llm_model == "deepseek-r1:latest":
            object.__setattr__(self, "llm_model", self.ollama_model)


settings = Settings()
