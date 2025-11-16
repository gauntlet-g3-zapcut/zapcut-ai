from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import time
from app.config import settings
from app.api import auth, brands, chat, campaigns

app = FastAPI(title="AdCraft API", version="1.0.0")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming API requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get request details
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        full_path = f"{path}?{query_params}" if query_params else path
        
        # Get origin header (for CORS debugging)
        origin = request.headers.get("origin", "none")
        
        # Get authorization header (masked for security)
        auth_header = request.headers.get("authorization", "none")
        if auth_header != "none":
            # Show first 20 chars and last 4 chars, mask the rest
            if len(auth_header) > 24:
                auth_preview = f"{auth_header[:20]}...{auth_header[-4:]}"
            else:
                auth_preview = "***masked***"
        else:
            auth_preview = "none"
        
        # Timestamp
        timestamp = datetime.utcnow().isoformat()
        
        # Log the incoming request
        print(f"[{timestamp}] 📥 {method} {full_path} | IP: {client_ip} | Origin: {origin} | Auth: {auth_preview}")
        
        # Process request and measure time
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            status_code = response.status_code
            print(f"[{timestamp}] 📤 {method} {full_path} | Status: {status_code} | Time: {process_time:.3f}s")
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            print(f"[{timestamp}] ❌ {method} {full_path} | Error: {str(e)} | Time: {process_time:.3f}s")
            raise


# Add request logging middleware (before CORS so we log all requests including preflight)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware - specify exact origins for credentialed requests
# Always includes production frontend and localhost for development
default_origins = [
    "https://app.zapcut.video",  # Production frontend (old)
    "https://frontend-adcraft-production.up.railway.app",  # Production frontend (new)
    "http://localhost:5173",     # Local development
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
]

# Merge with any additional origins from CORS_ORIGINS env var
env_origins = settings.cors_origins_list if settings.cors_origins_list else []
cors_origins = list(set(default_origins + env_origins))  # Combine and remove duplicates

# Log CORS origins for debugging (remove in production if needed)
print(f"🌐 CORS allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS for preflight
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
    from app.database import engine, Base
    from app.models.user import User
    from app.models.brand import Brand
    from app.models.creative_bible import CreativeBible
    from app.models.campaign import Campaign
    from app.models.generation_job import GenerationJob

    try:
        Base.metadata.create_all(bind=engine)
        return {
            "status": "success",
            "message": "Database tables created",
            "tables": list(Base.metadata.tables.keys())
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

