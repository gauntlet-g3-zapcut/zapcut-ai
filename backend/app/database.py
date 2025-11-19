"""Database configuration and session management."""
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        try:
            db_url = settings.database_url
            masked_url = db_url.split('@')[-1] if '@' in db_url else db_url
            logger.info(f"Creating database engine: postgresql://***@{masked_url}")

            # Configure engine with proper connection pooling and prepared statement handling
            _engine = create_engine(
                db_url,
                pool_pre_ping=True,  # Verify connections before using them
                pool_recycle=3600,   # Recycle connections after 1 hour
                connect_args={
                    "prepare_threshold": None  # Disable prepared statements to avoid naming conflicts
                }
            )
            logger.info("Database engine created")
        except ValueError as e:
            logger.error(f"Database configuration error: {e}")
            raise
    return _engine


def get_session_local():
    """Get or create session maker."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db():
    """Dependency for getting database session."""
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()

