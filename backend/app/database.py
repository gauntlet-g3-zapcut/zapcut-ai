from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

Base = declarative_base()

# Lazy initialization - only create engine when needed
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine (lazy initialization)"""
    global _engine
    if _engine is None:
        try:
            _engine = create_engine(settings.database_url)
        except ValueError as e:
            # If database URL can't be constructed, create a dummy engine
            # This allows the app to start but database operations will fail
            print(f"⚠️  Database URL not configured: {e}")
            print("⚠️  App will start but database operations will fail")
            # Create a dummy engine that will fail on actual use
            _engine = create_engine("postgresql://dummy:dummy@localhost:5432/dummy")
    return _engine


def get_session_local():
    """Get or create the session maker (lazy initialization)"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db():
    """Dependency for getting database session"""
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


