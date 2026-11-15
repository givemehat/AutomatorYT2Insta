import uuid
import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class Clip(Base):
    __tablename__ = "clips"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    youtube_id = Column(String(64), ForeignKey("youtube_videos.youtube_id", ondelete="CASCADE"), nullable=False, index=True)
    
    clip_title = Column(String(512), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    
    # AI Decision metadata
    decision_type = Column(String(64), nullable=False)  # POST_FULL_REEL, POST_SHORT_CLIP, POST_MULTIPLE_CLIPS, SKIP, REQUIRE_REVIEW
    ai_confidence = Column(Float, nullable=False)
    ai_reasoning = Column(Text, nullable=True)
    content_type = Column(String(64), nullable=True)  # educational, entertainment, hook, tutorial, etc.
    virality_score = Column(Float, default=0.0)
    
    # Generated Media Assets
    local_clip_path = Column(String(1024), nullable=True)
    subtitle_path = Column(String(1024), nullable=True)
    cloud_url = Column(String(1024), nullable=True)
    
    # AI Content
    caption = Column(Text, nullable=True)
    hashtags = Column(JSON, nullable=True)  # List of strings
    
    # Quality Control
    qc_status = Column(String(32), default="PENDING")  # PENDING, PASS, FAIL
    qc_details = Column(JSON, nullable=True)
    
    # Human Review & Publishing Gate
    approval_status = Column(String(32), default="PENDING_APPROVAL", index=True)  # PENDING_APPROVAL, APPROVED, REJECTED, AUTO_APPROVED

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    video = relationship("YouTubeVideo", back_populates="clips")
    instagram_post = relationship("InstagramPost", back_populates="clip", uselist=False, cascade="all, delete-orphan")
