from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    sandbox_url: str = "http://sandbox:8000"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    max_code_length: int = 20000
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"

    class Config:
        env_file = ".env"


settings = Settings()