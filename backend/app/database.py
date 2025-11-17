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
            _engine = create_engine(db_url)
            logger.info("Database engine created")
        except ValueError as e:
            logger.error(f"Database configuration error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}", exc_info=True)
            raise
    return _engine


def get_session_local():
    """Get or create session maker."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


# Lazy initialization - only create engine when accessed
# This allows the app to start even if database is temporarily unavailable
class _LazyEngine:
    """Lazy engine that creates connection only when accessed."""
    def __getattr__(self, name):
        return getattr(get_engine(), name)
    
    def __call__(self, *args, **kwargs):
        return get_engine()(*args, **kwargs)


engine = _LazyEngine()

# SessionLocal is created lazily via get_session_local()
# For direct imports, we provide a callable that creates sessions
def _create_session():
    """Create a new database session."""
    return get_session_local()()


# For backward compatibility - SessionLocal() should work
# We make it a callable that returns sessions
class _LazySessionLocal:
    """Lazy session maker that creates sessions when called."""
    def __call__(self, *args, **kwargs):
        return get_session_local()(*args, **kwargs)
    
    def __getattr__(self, name):
        return getattr(get_session_local(), name)


SessionLocal = _LazySessionLocal()


def get_db():
    """Dependency for getting database session."""
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()

