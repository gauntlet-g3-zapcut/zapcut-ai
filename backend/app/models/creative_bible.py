"""Creative Bible model."""
import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CreativeBible(Base):
    """Creative Bible model."""
    __tablename__ = "creative_bibles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    name = Column(String, nullable=False)
    creative_bible = Column(JSON, nullable=False, default=dict)
    original_creative_bible = Column(JSON, nullable=True)  # For revert functionality
    reference_image_urls = Column(JSON, nullable=False, default=dict)
    campaign_preferences = Column(JSON, nullable=True)  # Form answers: style, audience, emotion, pacing, colors, generation_mode, video_resolution, video_model, ideas
    created_at = Column(DateTime(timezone=False), nullable=False)
    updated_at = Column(DateTime(timezone=False), nullable=True, onupdate=func.now())  # For optimistic locking
    
    # Chat-based preference storage
    audience_description = Column(String, nullable=True)
    audience_keywords = Column(JSON, nullable=True)
    style_description = Column(String, nullable=True)
    style_keywords = Column(JSON, nullable=True)
    emotion_description = Column(String, nullable=True)
    emotion_keywords = Column(JSON, nullable=True)
    pacing_description = Column(String, nullable=True)
    pacing_keywords = Column(JSON, nullable=True)
    colors_description = Column(String, nullable=True)
    colors_keywords = Column(JSON, nullable=True)
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="creative_bible")
    chat_messages = relationship("ChatMessage", back_populates="creative_bible", cascade="all, delete-orphan")

