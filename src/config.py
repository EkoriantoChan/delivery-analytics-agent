"""Configuration management for Analytics Agent."""

from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    AGENT_API_URL: str = "http://localhost:8000"
    GOLD_DATABASE_URL: str = ""
    
    # LLM Provider Configuration ("openai" | "gemini" | "auto")
    LLM_PROVIDER: str = "auto"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5.6-luna"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # Demo tokens mapping
    DEMO_TOKEN_A: str = "token-alice-demo-secret-123"
    DEMO_TOKEN_B: str = "token-bob-demo-secret-456"

    # SQLite conversation store path
    SQLITE_PATH: str = "./data/conversations.sqlite3"

    # Database query execution limits
    DB_QUERY_TIMEOUT_SECONDS: int = 5
    DB_MAX_ROWS: int = 100

    # RAG Vector Store & Policies
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    POLICIES_DIR: str = "./docs/policies"

    # Agent constraints
    MAX_MESSAGE_HISTORY: int = 10
    MAX_PROMPT_LENGTH: int = 2000


settings = Settings()
