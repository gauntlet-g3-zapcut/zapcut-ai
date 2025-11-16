"""Campaign model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Campaign(Base):
    """Campaign model."""
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False, index=True)
    creative_bible_id = Column(UUID(as_uuid=True), ForeignKey("creative_bibles.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="pending", index=True)  # pending, generating, completed, failed
    storyline = Column(JSONB, nullable=True)  # Full storyline/script with scenes (populated during chat/script phase)
    sora_prompts = Column(JSONB, nullable=True, default=list)  # Array of 5 prompts (populated during script phase)
    suno_prompt = Column(Text, nullable=True)  # Music prompt (populated during script phase)
    video_urls = Column(JSONB, nullable=True)  # {scene_1, scene_2, ..., scene_5} S3 URLs
    voiceover_urls = Column(JSONB, nullable=True)  # Array of voiceover URLs per scene
    music_url = Column(String, nullable=True)  # S3 URL
    final_video_url = Column(String, nullable=True)  # S3 URL (populated after generation)
    task_group_id = Column(String, nullable=True)  # Celery group ID for tracking parallel tasks
    generation_stage = Column(String(50), default="not_started")  # Current pipeline stage
    generation_progress = Column(Integer, default=0)  # Progress percentage 0-100
    generation_logs = Column(JSONB, default=list)  # Array of log messages for streaming to frontend
    audio_url = Column(String, nullable=True)
    audio_status = Column(String, nullable=True, default="pending")  # pending/generating/completed/failed
    audio_generation_error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    brand = relationship("Brand", back_populates="campaigns")
    creative_bible = relationship("CreativeBible", back_populates="campaigns")
    generation_jobs = relationship("GenerationJob", back_populates="campaign", cascade="all, delete-orphan")

