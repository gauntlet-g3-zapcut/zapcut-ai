from pydantic_settings import BaseSettings
from typing import List, Optional, Union
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Replicate
    REPLICATE_API_TOKEN: Optional[str] = None
    
    # AWS S3 / Cloudflare R2 / Compatible Storage
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: str = "auto"
    AWS_ENDPOINT_URL: Optional[str] = None  # For R2: https://abc123.r2.cloudflarestorage.com
    R2_PUBLIC_URL: Optional[str] = None  # For R2 public domain: https://pub-xxx.r2.dev
    
    # Supabase
    SUPABASE_URL: Optional[str] = None
    
    # API
    API_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Initialize settings with environment variables
settings = Settings()


