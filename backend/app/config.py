"""Application configuration from environment variables."""
import re
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from urllib.parse import quote_plus


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: Optional[str] = None
    SUPABASE_URL: Optional[str] = None
    SUPABASE_DB_PASSWORD: Optional[str] = None
    
    # Supabase Auth
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    
    # Supabase S3 Storage
    SUPABASE_S3_ENDPOINT: Optional[str] = None
    SUPABASE_S3_ACCESS_KEY: Optional[str] = None
    SUPABASE_S3_SECRET_KEY: Optional[str] = None
    SUPABASE_S3_VIDEO_BUCKET: str = "videos"  # Bucket name for storing generated videos
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    REPLICATE_API_TOKEN: Optional[str] = None
    REPLICATE_WEBHOOK_SECRET: Optional[str] = None
    REPLICATE_VEO_3_1_VERSION: str = "google/veo-3.1"
    REPLICATE_KLING_2_1_VERSION: str = "kling/kling-2.1"
    REPLICATE_MINIMAX_VIDEO_01_VERSION: str = "minimax/video-01"
    REPLICATE_DEFAULT_VIDEO_MODEL: str = "google-veo-3-1"
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # API Configuration
    API_URL: Optional[str] = None  # Base URL for webhook callbacks (e.g., https://zapcut-api.fly.dev)
    
    # Celery/Redis
    REDIS_URL: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000,https://app.zapcut.video"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def database_url(self) -> str:
        """Get database URL, constructing from Supabase if needed."""
        if self.DATABASE_URL:
            # Check if DATABASE_URL is actually a Supabase URL (starts with https://)
            if self.DATABASE_URL.startswith(('https://', 'http://')):
                # If it looks like a Supabase URL, extract project ref and construct DB URL
                if self.SUPABASE_DB_PASSWORD:
                    # Remove protocol and extract project ref (first part before first dot)
                    project_ref = self.DATABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
                    encoded_password = quote_plus(self.SUPABASE_DB_PASSWORD)
                    return f"postgresql+psycopg://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"
                else:
                    raise ValueError(
                        "DATABASE_URL appears to be a Supabase URL (starts with https://), "
                        "but SUPABASE_DB_PASSWORD is not set. Either provide a proper PostgreSQL "
                        "connection string in DATABASE_URL, or set SUPABASE_URL and SUPABASE_DB_PASSWORD."
                    )
            
            # Check if DATABASE_URL contains https:// or http:// in the host part (malformed URL)
            # This handles cases like: postgresql://user:pass@https://host.com
            if '@https://' in self.DATABASE_URL or '@http://' in self.DATABASE_URL:
                # Remove the protocol from the host part
                cleaned_url = re.sub(r'@https?://', '@', self.DATABASE_URL)
                # Convert postgresql:// to postgresql+psycopg:// for psycopg3
                if cleaned_url.startswith(('postgresql://', 'postgres://')):
                    return cleaned_url.replace('postgresql://', 'postgresql+psycopg://').replace('postgres://', 'postgresql+psycopg://')
            
            # Convert postgresql:// to postgresql+psycopg:// for psycopg3
            if self.DATABASE_URL.startswith(('postgresql://', 'postgres://')):
                return self.DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://').replace('postgres://', 'postgresql+psycopg://')
            
            # If DATABASE_URL doesn't start with a known protocol, raise an error
            raise ValueError(
                f"DATABASE_URL must start with 'postgresql://', 'postgres://', or be a Supabase URL. "
                f"Got: {self.DATABASE_URL[:50]}..."
            )
        
        if self.SUPABASE_URL and self.SUPABASE_DB_PASSWORD:
            project_ref = self.SUPABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
            encoded_password = quote_plus(self.SUPABASE_DB_PASSWORD)
            return f"postgresql+psycopg://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"
        
        raise ValueError(
            "DATABASE_URL is required. Set DATABASE_URL or provide SUPABASE_URL and SUPABASE_DB_PASSWORD."
        )


settings = Settings()

