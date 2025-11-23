"""User model."""
import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supabase_uid = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False)

