"""Campaign model."""
import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
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
    images = Column(JSON, nullable=True, default=list)  # Reference/inspiration images for video generation
    video_urls = Column(JSON, nullable=True)
    music_url = Column(String, nullable=True)
    final_video_url = Column(String, nullable=True)
    task_group_id = Column(String, nullable=True)  # Celery group ID for tracking parallel tasks
    audio_url = Column(String, nullable=True)
    audio_status = Column(String, nullable=True, default="pending")  # pending/generating/completed/failed
    audio_generation_error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False)

    # Pipeline Version Control
    # v0: Original Sora 2 text-to-video (openai/sora-2), durations 4/8/12s + ElevenLabs music
    # v0.5: Veo 3.1 text-to-video (google/veo-3.1), durations 4/6/8s + ElevenLabs music
    # v1: Image-first parallel (Nano Banana → Real-ESRGAN → Veo 3.1 image-to-video) + ElevenLabs music
    # v2: Story-first sequential (GPT-4o story → ElevenLabs voiceover → Nano Banana → Veo 3.1 with frame seeding)
    # v2p: Story-first PARALLEL (GPT-4o story → character ref → all scenes parallel → all videos parallel)
    pipeline_version = Column(String, default="v2p")  # "v0", "v0.5", "v1", "v2", or "v2p"

    # V2 Pipeline Fields - Story-first sequential generation
    story_document = Column(JSON, nullable=True)  # Full story with characters, narrator, segments
    voiceover_url = Column(String, nullable=True)  # ElevenLabs TTS full narration audio
    voiceover_status = Column(String, nullable=True, default="pending")  # pending/generating/completed/failed
    final_audio_url = Column(String, nullable=True)  # Mixed voiceover + music
    current_segment = Column(Integer, default=0)  # Track sequential video progress (1-5)

    # Phase 1 pipeline fields (kept for backward compatibility)
    pipeline_stage = Column(String, nullable=True)  # prompts_generating, images_generating, etc.
    director_mode = Column(String, nullable=True)  # surprise_me or director
    image_prompts = Column(JSON, nullable=True)  # Enhanced prompts from GPT-4o

    # Relationships
    brand = relationship("Brand", back_populates="campaigns")
    creative_bible = relationship("CreativeBible", back_populates="campaigns")

