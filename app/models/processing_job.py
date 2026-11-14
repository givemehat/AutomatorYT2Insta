import uuid
import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    youtube_id = Column(String(64), ForeignKey("youtube_videos.youtube_id", ondelete="CASCADE"), nullable=False, index=True)
    
    stage = Column(String(64), nullable=False)  # INGESTION, TRANSCRIPTION, AI_ANALYSIS, VIDEO_PROCESSING, QC, PUBLISH
    status = Column(String(32), default="PENDING", index=True)  # PENDING, RUNNING, COMPLETED, FAILED, RETRYING
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    metadata_payload = Column(JSON, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    # Relationship
    video = relationship("YouTubeVideo", back_populates="jobs")
