from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "BoardAndGo fastapi service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    
    RAPID_API_KEY: str
    
    DEBUG: bool = False
    
    FR24_API_KEY: str = ""
    FR24_BASE_URL: str = "https://fr24api.flightradar24.com/api/"
    FR24_API_VERSION: str = "v1"
    
    # MongoDB Settings
    MONGODB_URL: str
    DB_NAME: str = "BoardAndGo"
    
    # External API Configuration
    AVIATION_STACK_API_KEY: str =""
    AVIATION_API_URL: str = "https://api.aviationstack.com/v1/flights"
    API_TIMEOUT: int = 30
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    
    class Config:
        env_file = ".env"

settings = Settings()
