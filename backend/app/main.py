from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth, brands, chat, campaigns

app = FastAPI(title="AdCraft API", version="1.0.0")

# CORS middleware - specify exact origins for credentialed requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://adcraft-blond.vercel.app",
        "https://frontend-inalnorox-natalyscst-gmailcoms-projects.vercel.app",
        "https://frontend-etezftdsl-natalyscst-gmailcoms-projects.vercel.app",
        "https://frontend-qpw6399ey-natalyscst-gmailcoms-projects.vercel.app",
        "http://localhost:5173",
        "http://localhost:5175",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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


@app.post("/init-db")
async def init_database():
    """Initialize database tables (one-time setup)"""
    from app.database import engine, Base
    from app.models.user import User
    from app.models.brand import Brand
    from app.models.creative_bible import CreativeBible
    from app.models.campaign import Campaign
    
    try:
        Base.metadata.create_all(bind=engine)
        return {
            "status": "success",
            "message": "Database tables created",
            "tables": list(Base.metadata.tables.keys())
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

