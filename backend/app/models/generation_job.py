from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)  # 'scene_video', 'voiceover', 'music', 'composite'
    scene_number = Column(Integer, nullable=True)  # For scene-specific jobs
    status = Column(String(50), nullable=False, default="pending", index=True)  # 'pending', 'processing', 'completed', 'failed'
    replicate_job_id = Column(String(255), nullable=True)
    input_params = Column(JSONB, nullable=True)
    output_url = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    campaign = relationship("Campaign", back_populates="generation_jobs")

    __table_args__ = (
        Index('idx_generation_jobs_campaign', 'campaign_id'),
        Index('idx_generation_jobs_status', 'status'),
    )
