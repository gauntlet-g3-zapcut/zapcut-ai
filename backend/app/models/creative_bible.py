from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base


class CreativeBible(Base):
    __tablename__ = "creative_bibles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    creative_bible = Column(JSONB, nullable=False)  # {colors, vibe, style, lighting, camera, motion, energy_level}
    reference_image_urls = Column(JSONB, nullable=False)  # {user_1, user_2, hero, detail, lifestyle, alternate}
    conversation_history = Column(JSONB)  # Q&A conversation
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    brand = relationship("Brand", back_populates="creative_bibles")
    campaigns = relationship("Campaign", back_populates="creative_bible")

    __table_args__ = (
        UniqueConstraint("brand_id", "name", name="uq_brand_creative_bible_name"),
    )


