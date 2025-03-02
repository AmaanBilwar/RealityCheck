from pydantic import BaseSettings

class Settings(BaseSettings):
    # FastAPI server settings
    API_TITLE: str = "Chatbot API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API for the Chatbot application"
    API_PREFIX: str = "/api"

    # Database settings (if applicable)
    DATABASE_URL: str = "sqlite:///./test.db"

    class Config:
        env_file = ".env"

settings = Settings()