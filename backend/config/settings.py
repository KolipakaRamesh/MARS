"""
MARS — Centralized settings via Pydantic BaseSettings.
All values read from environment / .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── LLM ──────────────────────────────────────────────────────────────────
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # ── Agent Models ─────────────────────────────────────────────────────────
    planner_model: str = "meta-llama/llama-3.2-3b-instruct"
    research_model: str = "meta-llama/llama-3.1-8b-instruct"
    analyst_model:  str = "meta-llama/llama-3.1-8b-instruct"   # switched from 70B for speed
    reviewer_model: str = "meta-llama/llama-3.1-8b-instruct"

    # ── Orchestration ────────────────────────────────────────────────────────
    max_iterations: int = 2    # reduced from 3 to cut retry latency
    quality_threshold: float = 0.75
    max_react_steps: int = 3   # reduced from 5; saves 2 LLM calls per subtask

    # ── Memory ───────────────────────────────────────────────────────────────
    memory_ttl_days: int = 90
    memory_top_k: int = 3

    # ── Convex ───────────────────────────────────────────────────────────────
    convex_url: str | None = Field(None, env="CONVEX_URL")
    convex_deploy_key: str | None = Field(None, env="CONVEX_DEPLOY_KEY")

    # ── Observability ────────────────────────────────────────────────────────
    opik_api_key: str | None = Field(None, env="OPIK_API_KEY")
    opik_project_name: str = "MARS"
    opik_workspace: str | None = Field(None, env="OPIK_WORKSPACE")
    opik_url_override: str | None = Field(None, env="OPIK_URL_OVERRIDE")
    opik_use_local: bool = False

    # ── API ──────────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton — import this everywhere
settings = Settings()
