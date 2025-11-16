from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from urllib.parse import quote_plus


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Core required environment variables:
    - DATABASE_URL: PostgreSQL connection string (or constructed from Supabase)
    - OPENAI_API_KEY: OpenAI API key for AI features
    - REPLICATE_API_TOKEN: Replicate API token for video/image generation (Sora, Suno, etc.)
    - SUPABASE_URL: Supabase project URL
    - SUPABASE_SERVICE_ROLE_KEY: Supabase service role key for admin operations
    - SUPABASE_DB_PASSWORD: Supabase database password (used if DATABASE_URL not set)
    """
    
    # Core Database Configuration
    DATABASE_URL: Optional[str] = None
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    
    # Replicate Configuration
    REPLICATE_API_TOKEN: Optional[str] = None
    
    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_DB_PASSWORD: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None  # For HS256 token verification (legacy)
    
    # Supabase Storage S3 Configuration
    SUPABASE_S3_ENDPOINT: Optional[str] = None
    SUPABASE_S3_ACCESS_KEY: Optional[str] = None  # Usually the project ref
    SUPABASE_S3_SECRET_KEY: Optional[str] = None  # Usually the service role key
    
    # Redis Configuration (for Celery)
    REDIS_URL: Optional[str] = None
    
    # API Configuration
    API_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str = "http://localhost:5174,http://localhost:5173,http://localhost:3000,https://frontend-adcraft-production.up.railway.app"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables (like PORT which is used by uvicorn)
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def database_url(self) -> str:
        """
        Get database URL, constructing from Supabase credentials if needed.
        
        Priority:
        1. Use DATABASE_URL if it's a valid PostgreSQL connection string
        2. Construct from SUPABASE_URL and SUPABASE_DB_PASSWORD if available
        3. Raise error if neither is available
        
        Supabase DATABASE_URL format: 
        postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
        """
        # If DATABASE_URL is set and is a valid PostgreSQL connection string, use it
        if self.DATABASE_URL and self.DATABASE_URL.startswith(('postgresql://', 'postgres://')):
            return self.DATABASE_URL
        
        # Construct from Supabase credentials if available
        if self.SUPABASE_URL and self.SUPABASE_DB_PASSWORD:
            # Extract project ref from SUPABASE_URL (e.g., https://rksxuhhegcxqmkjopudx.supabase.co)
            project_ref = self.SUPABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
            # Construct PostgreSQL connection string with URL-encoded password
            encoded_password = quote_plus(self.SUPABASE_DB_PASSWORD)
            return f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"
        
        # Raise error if no valid database URL can be constructed
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


