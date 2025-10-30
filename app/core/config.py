import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database (Cloud SQL IAM auth configured in app/db/database.py)
    # No DATABASE_URL needed here for Cloud Run - it's built from env vars
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    
    # SMTP Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_EMAIL: str = os.getenv("SMTP_EMAIL", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    FRONTEND_URL_8081: str = os.getenv("FRONTEND_URL_8081", "http://localhost:8081")
    
    # OTP Configuration
    OTP_EXPIRY_MINUTES: int = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
    RESET_TOKEN_EXPIRY_MINUTES: int = int(os.getenv("RESET_TOKEN_EXPIRY_MINUTES", "15"))
    
    # Development
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()