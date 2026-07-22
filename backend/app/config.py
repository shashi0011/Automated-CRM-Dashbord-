from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "gemma2-9b-it"
    groq_model_fallback: str = "llama-3.3-70b-versatile"
    database_url: str = "sqlite:///./hcp_crm.db"

    class Config:
        env_file = ".env"


settings = Settings()
