"""Application configuration from environment variables."""
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
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    REPLICATE_API_TOKEN: Optional[str] = None
    REPLICATE_WEBHOOK_SECRET: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # API Configuration
    API_URL: Optional[str] = None  # Base URL for webhook callbacks (e.g., https://your-api.railway.app or custom domain)
    
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
        if self.DATABASE_URL and self.DATABASE_URL.startswith(('postgresql://', 'postgres://')):
            return self.DATABASE_URL
        
        if self.SUPABASE_URL and self.SUPABASE_DB_PASSWORD:
            project_ref = self.SUPABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
            encoded_password = quote_plus(self.SUPABASE_DB_PASSWORD)
            return f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"
        
        raise ValueError(
            "DATABASE_URL is required. Set DATABASE_URL or provide SUPABASE_URL and SUPABASE_DB_PASSWORD."
        )


settings = Settings()

