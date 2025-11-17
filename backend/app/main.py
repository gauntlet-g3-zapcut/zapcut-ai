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

# Regex pattern to allow all subdomains of zapcut-app.pages.dev
PAGES_DEV_SUBDOMAIN_REGEX = r"https://.*\.zapcut-app\.pages\.dev"

logger.info(f"CORS allowed origins: {cors_origins}")
logger.info(f"CORS allowed origin regex: {PAGES_DEV_SUBDOMAIN_REGEX}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=PAGES_DEV_SUBDOMAIN_REGEX,
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


@app.post("/migrate-chat-columns")
async def migrate_chat_columns():
    """Add chat-related columns to creative_bibles table and create chat_messages table (migration)."""
    try:
        from app.database import get_engine
        from sqlalchemy import text
        
        engine = get_engine()
        
        with engine.begin() as conn:
            migration_sql = """
            DO $$ 
            BEGIN
                -- Add preference description columns to creative_bibles if they don't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'creative_bibles' AND column_name = 'audience_description'
                ) THEN
                    ALTER TABLE creative_bibles ADD COLUMN audience_description VARCHAR;
                    RAISE NOTICE 'Added audience_description column';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'creative_bibles' AND column_name = 'audience_keywords'
                ) THEN
                    ALTER TABLE creative_bibles ADD COLUMN audience_keywords JSONB;
                    RAISE NOTICE 'Added audience_keywords column';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'creative_bibles' AND column_name = 'style_description'
                ) THEN
                    ALTER TABLE creative_bibles ADD COLUMN style_description VARCHAR;
                    RAISE NOTICE 'Added style_description column';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'creative_bibles' AND column_name = 'style_keywords'
                ) THEN
                    ALTER TABLE creative_bibles ADD COLUMN style_keywords JSONB;
                    RAISE NOTICE 'Added style_keywords column';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'creative_bibles' AND column_name = 'emotion_description'
                ) THEN
                    ALTER TABLE creative_bibles ADD COLUMN emotion_description VARCHAR;
                    RAISE NOTICE 'Added emotion_description column';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'creative_bibles' AND column_name = 'emotion_keywords'
                ) THEN
                    ALTER TABLE creative_bibles ADD COLUMN emotion_keywords JSONB;
                    RAISE NOTICE 'Added emotion_keywords column';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'creative_bibles' AND column_name = 'pacing_description'
                ) THEN
                    ALTER TABLE creative_bibles ADD COLUMN pacing_description VARCHAR;
                    RAISE NOTICE 'Added pacing_description column';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'creative_bibles' AND column_name = 'pacing_keywords'
                ) THEN
                    ALTER TABLE creative_bibles ADD COLUMN pacing_keywords JSONB;
                    RAISE NOTICE 'Added pacing_keywords column';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'creative_bibles' AND column_name = 'colors_description'
                ) THEN
                    ALTER TABLE creative_bibles ADD COLUMN colors_description VARCHAR;
                    RAISE NOTICE 'Added colors_description column';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'creative_bibles' AND column_name = 'colors_keywords'
                ) THEN
                    ALTER TABLE creative_bibles ADD COLUMN colors_keywords JSONB;
                    RAISE NOTICE 'Added colors_keywords column';
                END IF;
            END $$;
            """
            
            conn.execute(text(migration_sql))
            
            # Create chat_messages table if it doesn't exist
            create_chat_messages_table = """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                creative_bible_id UUID NOT NULL REFERENCES creative_bibles(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_chat_messages_creative_bible_id 
            ON chat_messages(creative_bible_id);
            
            CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at 
            ON chat_messages(created_at);
            """
            
            conn.execute(text(create_chat_messages_table))
            
        logger.info("Chat columns migration completed successfully")
        
        return {
            "status": "success",
            "message": "Chat columns added to creative_bibles table and chat_messages table created",
            "columns_added": [
                "audience_description", "audience_keywords",
                "style_description", "style_keywords",
                "emotion_description", "emotion_keywords",
                "pacing_description", "pacing_keywords",
                "colors_description", "colors_keywords"
            ],
            "tables_created": ["chat_messages"]
        }
    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

