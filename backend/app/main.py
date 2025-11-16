from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth, brands, chat, campaigns

app = FastAPI(title="AdCraft API", version="1.0.0")

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
    print(f"⚠️  Production frontend was missing from CORS origins, added: {PRODUCTION_FRONTEND}")

# Log CORS origins for debugging
print(f"🌐 CORS allowed origins: {cors_origins}")

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
