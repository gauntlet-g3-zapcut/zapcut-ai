import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Lazy initialization - only create engine when needed
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine (lazy initialization)"""
    global _engine
    if _engine is None:
        try:
            db_url = settings.database_url
            # Mask password in logs for security
            masked_url = db_url.split('@')[-1] if '@' in db_url else db_url
            logger.info(f"Creating database engine: postgresql://***@{masked_url}")
            _engine = create_engine(db_url)
            logger.info("Database engine created successfully")
        except ValueError as e:
            logger.error(f"Database configuration error: {e}")
            # Fail fast with clear error message
            raise ValueError(
                f"Database configuration error: {e}\n"
                "Please set DATABASE_URL or provide SUPABASE_URL and SUPABASE_DB_PASSWORD"
            ) from e
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


