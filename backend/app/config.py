from pydantic_settings import BaseSettings
from typing import List, Optional, Union
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: Optional[str] = None
    
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
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_DB_PASSWORD: Optional[str] = None
    
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
    
    @property
    def database_url(self) -> str:
        """
        Get database URL, constructing from Supabase credentials if needed.
        Supabase DATABASE_URL format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
        """
        # If DATABASE_URL is set and is a valid PostgreSQL connection string, use it
        if self.DATABASE_URL and self.DATABASE_URL.startswith(('postgresql://', 'postgres://')):
            return self.DATABASE_URL
        
        # If DATABASE_URL is set but invalid (e.g., HTTPS URL), try to construct from Supabase
        if self.SUPABASE_URL and self.SUPABASE_DB_PASSWORD:
            # Extract project ref from SUPABASE_URL (e.g., https://rksxuhhegcxqmkjopudx.supabase.co)
            project_ref = self.SUPABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
            # Construct PostgreSQL connection string
            # URL encode password in case it has special characters
            from urllib.parse import quote_plus
            encoded_password = quote_plus(self.SUPABASE_DB_PASSWORD)
            return f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"
        
        # Fallback: raise error if no valid database URL can be constructed
        if not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL is required. Either set DATABASE_URL directly or provide "
                "SUPABASE_URL and SUPABASE_DB_PASSWORD to construct it."
            )
        
        raise ValueError(
            f"Invalid DATABASE_URL format: {self.DATABASE_URL}. "
            "Expected postgresql:// or postgres:// connection string."
        )


# Initialize settings with environment variables
settings = Settings()


