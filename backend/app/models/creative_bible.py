"""Creative Bible model."""
import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class CreativeBible(Base):
    """Creative Bible model."""
    __tablename__ = "creative_bibles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    name = Column(String, nullable=False)
    creative_bible = Column(JSON, nullable=False, default=dict)
    reference_image_urls = Column(JSON, nullable=False, default=dict)
    conversation_history = Column(JSON, nullable=True)
    created_at = Column(String, nullable=False)
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="creative_bible")

