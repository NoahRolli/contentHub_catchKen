from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "catchKen Content Hub"
    app_env: str = "development"
    database_url: str = "sqlite:///./catchken.db"
    secret_key: str = "change-me-to-random-string"
    
    # LLM
    ollama_base_url: str = "http://localhost:11434"
    openai_api_key: str = ""
    
    # Media
    media_path: str = "media/uploads"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()