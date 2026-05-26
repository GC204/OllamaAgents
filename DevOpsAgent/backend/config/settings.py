import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import time


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # GitHub
    github_pat_token: str
    github_api_base_url: str = "https://api.github.com"
    
    # Ollama
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    ollama_model: str = "gemma4"
    ollama_generate_timeout: int = 60  # seconds for generation requests
    ollama_pull_timeout: int = 300  # seconds for model pull requests
    ollama_check_timeout: int = 5  # seconds for availability checks
    ollama_max_retries: int = 2  # number of retries for failed requests
    
    # Backend
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./data/devops_agent.db"
    
    # CORS
    allowed_origins: str | list = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]
    
    # Session
    session_timeout_minutes: int = 1440
    max_chat_history: int = 100
    
    class Config:
        env_file = "../.env"
        case_sensitive = False
        extra = "ignore"
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse allowed_origins from comma-separated string to list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def ollama_base_url(self) -> str:
        """Get Ollama base URL."""
        return f"http://{self.ollama_host}:{self.ollama_port}"
    
    @property
    def database_path(self) -> str:
        """Get database file path."""
        db_url = self.database_url
        if db_url.startswith("sqlite:///"):
            return db_url.replace("sqlite:///", "")
        return db_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
