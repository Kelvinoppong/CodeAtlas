"""
Application configuration
"""

import secrets
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CodeAtlas"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/codeatlas"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # AI/LLM
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    
    # Ollama (local LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:7b"
    AI_PROVIDER: str = "ollama"  # "ollama", "gemini", or "openai"
    
    # Storage
    PROJECTS_DIR: str = "./projects"
    
    # Redis (optional, for task queue and caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Cache settings
    CACHE_TTL: int = 300  # Default cache TTL in seconds
    CACHE_MAX_SIZE: int = 1000  # Max cache entries
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
