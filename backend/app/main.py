import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
    ]
)

logger = logging.getLogger(__name__)

# Add comprehensive error logging at the very start
def log_error_and_exit(msg, exc=None):
    """Log error and exit gracefully"""
    logger.error(f"FATAL ERROR: {msg}")
    if exc:
        logger.exception("Exception details:")
    sys.exit(1)

# Try to import with error handling
try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    logger.info("FastAPI imported successfully")
except ImportError as e:
    log_error_and_exit(f"Failed to import FastAPI: {e}", e)

try:
    from app.config import settings
    logger.info("Settings imported successfully")
except Exception as e:
    log_error_and_exit(f"Failed to import settings: {e}", e)

try:
    from app.api import auth, brands, chat, campaigns
    logger.info("API routers imported successfully")
except Exception as e:
    log_error_and_exit(f"Failed to import API routers: {e}", e)

try:
    app = FastAPI(title="AdCraft API", version="1.0.0")
    logger.info("FastAPI app created successfully")
except Exception as e:
    log_error_and_exit(f"Failed to create FastAPI app: {e}", e)

# CORS middleware - specify exact origins for credentialed requests
# CRITICAL: Always includes production frontend - this must never be removed
PRODUCTION_FRONTEND = "https://app.zapcut.video"

default_origins = [
    PRODUCTION_FRONTEND,  # Production frontend - REQUIRED
    "http://localhost:5173",     # Local development
    "http://localhost:5175",
    "http://localhost:3000",
]

# Merge with any additional origins from CORS_ORIGINS env var
env_origins = settings.cors_origins_list if settings.cors_origins_list else []
cors_origins = list(set(default_origins + env_origins))  # Combine and remove duplicates

# Ensure production frontend is always included (safety check)
if PRODUCTION_FRONTEND not in cors_origins:
    cors_origins.append(PRODUCTION_FRONTEND)
    logger.warning(f"Production frontend was missing from CORS origins, added: {PRODUCTION_FRONTEND}")

# Log CORS origins for debugging
logger.info(f"CORS allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicit methods
    allow_headers=["*"],   # Allow all headers including Content-Type, Authorization
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Include routers
app.include_router(auth.router)
app.include_router(brands.router)
app.include_router(chat.router)
app.include_router(campaigns.router)


@app.get("/")
async def root():
    return {"message": "AdCraft API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/cors-info")
async def cors_info():
    """Debug endpoint to check CORS configuration"""
    return {
        "cors_origins": cors_origins,
        "default_origins": default_origins,
        "env_origins": env_origins,
        "settings_cors_origins": settings.CORS_ORIGINS,
    }


@app.post("/init-db")
async def init_database():
    """Initialize database tables (one-time setup)"""
    from app.database import get_engine, Base
    from app.models.user import User
    from app.models.brand import Brand
    from app.models.creative_bible import CreativeBible
    from app.models.campaign import Campaign
    
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        return {
            "status": "success",
            "message": "Database tables created",
            "tables": list(Base.metadata.tables.keys())
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
