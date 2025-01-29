from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Flight Agent Notification Fastapi "
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    AVIATIONSTACK_API_KEY: str
    GROQ_API_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_FROM_NUMBER: str
    AVIATION_STACK_KEY_6: str
    
    DEBUG: bool = False
    
    FR24_API_KEY: str
    FR24_BASE_URL: str = "https://fr24api.flightradar24.com/api/"
    FR24_API_VERSION: str = "v1"
    
    # MongoDB Settings
    MONGODB_URL: str
    DB_NAME: str = "BoardAndGo"
    
    
    class Config:
        env_file = ".env"

settings = Settings()
