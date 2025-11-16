"""Campaign model."""
import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Campaign(Base):
    """Campaign model."""
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    creative_bible_id = Column(UUID(as_uuid=True), ForeignKey("creative_bibles.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")
    storyline = Column(JSON, nullable=True)
    sora_prompts = Column(JSON, nullable=True, default=list)
    suno_prompt = Column(String, nullable=True)
    video_urls = Column(JSON, nullable=True)
    music_url = Column(String, nullable=True)
    final_video_url = Column(String, nullable=True)
    task_group_id = Column(String, nullable=True)  # Celery group ID for tracking parallel tasks
    created_at = Column(String, nullable=False)
    
    # Relationships
    brand = relationship("Brand", back_populates="campaigns")
    creative_bible = relationship("CreativeBible", back_populates="campaigns")

