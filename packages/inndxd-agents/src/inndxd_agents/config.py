from __future__ import annotations

from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    model_config = {"env_prefix": "INNDXD_", "env_file": ".env", "extra": "ignore"}

    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "deepseek-r1:latest"
    llm_provider_name: str = "default"

    ollama_base_url: str = ""
    ollama_model: str = ""

    planner_model: str | None = None
    collector_model: str | None = None
    structurer_model: str | None = None

    def model_post_init(self, __context: object) -> None:
        if self.ollama_base_url and self.llm_base_url == "http://localhost:11434/v1":
            object.__setattr__(self, "llm_base_url", self.ollama_base_url)
        if self.ollama_model and self.llm_model == "deepseek-r1:latest":
            object.__setattr__(self, "llm_model", self.ollama_model)


settings = AgentSettings()
