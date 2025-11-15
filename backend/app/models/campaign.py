from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False, index=True)
    creative_bible_id = Column(UUID(as_uuid=True), ForeignKey("creative_bibles.id"), nullable=False, index=True)
    storyline = Column(JSONB, nullable=False)  # Full storyline/script with scenes
    sora_prompts = Column(JSONB, nullable=False)  # Array of 5 prompts
    suno_prompt = Column(Text, nullable=False)
    video_urls = Column(JSONB)  # {scene_1, scene_2, ..., scene_5} S3 URLs
    music_url = Column(String)  # S3 URL
    final_video_url = Column(String, nullable=False)  # S3 URL
    status = Column(String, nullable=False, default="pending", index=True)  # pending, generating, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    brand = relationship("Brand", back_populates="campaigns")
    creative_bible = relationship("CreativeBible", back_populates="campaigns")


