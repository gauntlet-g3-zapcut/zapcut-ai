"""Brand model."""
import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Brand(Base):
    """Brand model."""
    __tablename__ = "brands"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    product_image_1_url = Column(String, nullable=True)
    product_image_2_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False)
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="brand")

