import uuid
import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class InstagramPost(Base):
    __tablename__ = "instagram_posts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clip_id = Column(String(36), ForeignKey("clips.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Meta Graph API references
    ig_container_id = Column(String(128), nullable=True, index=True)
    ig_media_id = Column(String(128), nullable=True, index=True)
    ig_permalink = Column(String(512), nullable=True)
    
    # State: SCHEDULED, UPLOADING, PROCESSING, PUBLISHED, FAILED
    publication_status = Column(String(32), default="PROCESSING", index=True)
    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    error_details = Column(Text, nullable=True)
    
    # Post analytics (likes, comments, views)
    performance_metrics = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    clip = relationship("Clip", back_populates="instagram_post")
