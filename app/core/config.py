from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # SMTP Configuration
    SMTP_SERVER: str
    SMTP_PORT: int = 587
    SMTP_EMAIL: str
    SMTP_PASSWORD: str
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    FRONTEND_URL_8081: str = "http://localhost:8081"
    
    # OTP Configuration
    OTP_EXPIRY_MINUTES: int = 10
    RESET_TOKEN_EXPIRY_MINUTES: int = 15
    
    # Development
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()