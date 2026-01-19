"""
Application configuration
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CodeAtlas"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/codeatlas"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # AI/LLM
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    
    # Storage
    PROJECTS_DIR: str = "./projects"
    
    # Redis (optional, for task queue)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
