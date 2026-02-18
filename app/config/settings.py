from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "NoaVoiceAI"
    DEBUG: bool = False
    
    # Cal.com V2
    CALCOM_API_KEY: str
    CALCOM_EVENT_TYPE_ID: int
    CALCOM_BASE_URL: str = "https://api.cal.com/v2"
    CALCOM_API_VERSION: str = "2024-08-13"
    
    # Neon PostgreSQL
    DATABASE_URL: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Single instance used everywhere
settings = Settings()