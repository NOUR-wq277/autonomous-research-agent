"""Configuration and application settings module."""

import os
from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    gemini_api_key: str = Field(
        default="",
        alias="GEMINI_API_KEY",
        description="Google Gemini API key for LLM calls and search grounding.",
    )

    # Model Configuration
    gemini_model: str = Field(
        default="gemini-3.5-flash-lite",
        alias="GEMINI_MODEL",
        description="Primary model for planning, research synthesis, and writing.",
    )
    fallback_models_str: str = Field(
        default="gemini-3.6-flash,gemini-flash-latest,gemini-2.5-flash",
        alias="FALLBACK_MODELS",
        description="Comma-separated fallback model names.",
    )

    # Research Parameters
    max_research_iterations: int = Field(
        default=3,
        alias="MAX_RESEARCH_ITERATIONS",
        description="Maximum iterations the verifier can route back to researcher.",
    )
    max_search_queries: int = Field(
        default=4,
        alias="MAX_SEARCH_QUERIES",
        description="Maximum search queries per iteration.",
    )
    max_sources_per_query: int = Field(
        default=5,
        alias="MAX_SOURCES_PER_QUERY",
        description="Maximum sources extracted per search query.",
    )

    # Server Configuration
    api_host: str = Field(
        default="0.0.0.0",
        alias="API_HOST",
        description="Host address for FastAPI server.",
    )
    api_port: int = Field(
        default=8000,
        alias="API_PORT",
        description="Port for FastAPI server.",
    )

    # Observability
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level.",
    )

    @property
    def fallback_models(self) -> List[str]:
        """Return fallback models as a cleaned list."""
        if not self.fallback_models_str:
            return []
        return [m.strip() for m in self.fallback_models_str.split(",") if m.strip()]

    def get_all_models(self) -> List[str]:
        """Return the primary model followed by fallback models without duplicates."""
        models = [self.gemini_model]
        for m in self.fallback_models:
            if m not in models:
                models.append(m)
        return models


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings."""
    return Settings()
