from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: Optional[str] = None
    api_url: str = "http://localhost:8080"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    max_code_length: int = 20000
    log_level: str = "INFO"
    log_format: str = "json"

    class Config:
        env_file = ".env"


settings = Settings()