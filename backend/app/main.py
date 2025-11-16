"""Main FastAPI application."""
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth, brands, chat, campaigns, webhooks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="AdCraft API", version="1.0.0")

# CORS configuration
PRODUCTION_FRONTEND = "https://app.zapcut.video"
default_origins = [
    PRODUCTION_FRONTEND,
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
]

env_origins = settings.cors_origins_list if settings.cors_origins_list else []
cors_origins = list(set(default_origins + env_origins))

if PRODUCTION_FRONTEND not in cors_origins:
    cors_origins.append(PRODUCTION_FRONTEND)
    logger.warning(f"Production frontend was missing from CORS origins, added: {PRODUCTION_FRONTEND}")

logger.info(f"CORS allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(auth.router)
app.include_router(brands.router)
app.include_router(chat.router)
app.include_router(campaigns.router)
app.include_router(webhooks.router)

logger.info("FastAPI app initialized successfully")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AdCraft API", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint for Fly.io load balancer.
    
    This endpoint MUST respond quickly (< 3s) and return 200 OK
    for Fly.io to route traffic to this machine.
    """
    return {"status": "ok", "service": "fastapi"}


@app.get("/cors-info")
async def cors_info():
    """Debug endpoint to check CORS configuration."""
    return {
        "cors_origins": cors_origins,
        "default_origins": default_origins,
        "env_origins": env_origins,
        "settings_cors_origins": settings.CORS_ORIGINS,
    }


@app.post("/init-db")
async def init_database():
    """Initialize database tables (one-time setup)."""
    try:
        from app.database import get_engine, Base
        from app.models import User, Brand, CreativeBible, Campaign
        
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully")
        
        return {
            "status": "success",
            "message": "Database tables created",
            "tables": list(Base.metadata.tables.keys())
        }
    except Exception as e:
        logger.error(f"Database initialization error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@app.post("/migrate-audio-columns")
async def migrate_audio_columns():
    """Add audio-related columns to campaigns table (migration)."""
    try:
        from app.database import get_engine
        from sqlalchemy import text
        
        engine = get_engine()
        
        with engine.begin() as conn:
            # Check if columns exist and add them if they don't
            migration_sql = """
            DO $$ 
            BEGIN
                -- Add audio_url column if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'campaigns' AND column_name = 'audio_url'
                ) THEN
                    ALTER TABLE campaigns ADD COLUMN audio_url VARCHAR;
                    RAISE NOTICE 'Added audio_url column';
                END IF;
                
                -- Add audio_status column if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'campaigns' AND column_name = 'audio_status'
                ) THEN
                    ALTER TABLE campaigns ADD COLUMN audio_status VARCHAR DEFAULT 'pending';
                    RAISE NOTICE 'Added audio_status column';
                END IF;
                
                -- Add audio_generation_error column if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'campaigns' AND column_name = 'audio_generation_error'
                ) THEN
                    ALTER TABLE campaigns ADD COLUMN audio_generation_error VARCHAR;
                    RAISE NOTICE 'Added audio_generation_error column';
                END IF;
            END $$;
            """
            
            conn.execute(text(migration_sql))
            
        logger.info("Audio columns migration completed successfully")
        
        return {
            "status": "success",
            "message": "Audio columns added to campaigns table",
            "columns_added": ["audio_url", "audio_status", "audio_generation_error"]
        }
    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

