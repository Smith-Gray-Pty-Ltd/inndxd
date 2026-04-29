from __future__ import annotations

from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    model_config = {"env_prefix": "INNDXD_", "env_file": ".env"}

    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "deepseek-r1:latest"


settings = AgentSettings()
