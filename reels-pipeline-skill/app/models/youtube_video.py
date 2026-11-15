import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class YouTubeVideo(Base):
    __tablename__ = "youtube_videos"

    youtube_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    published_at = Column(DateTime, nullable=True)
    channel_id = Column(String(64), nullable=True, index=True)
    thumbnail_url = Column(String(1024), nullable=True)
    
    # Enriched metadata & scraping info
    view_count = Column(Integer, nullable=True)
    like_count = Column(Integer, nullable=True)
    tags = Column(JSON, nullable=True)  # List of tag strings
    chapters = Column(JSON, nullable=True)  # List of {title, start_time}
    scraped_comments = Column(JSON, nullable=True)  # Top comments for audience context
    
    # Local files
    local_video_path = Column(String(1024), nullable=True)
    local_audio_path = Column(String(1024), nullable=True)
    
    # Transcripts
    transcript_raw = Column(Text, nullable=True)
    transcript_timestamps = Column(JSON, nullable=True)  # List of {start, end, text}
    
    # Pipeline status: DISCOVERED, DOWNLOADING, DOWNLOADED, TRANSCRIBING, TRANSCRIBED, ANALYSING, DECISION_MADE, PROCESSED, SKIPPED, FAILED
    processing_status = Column(String(64), default="DISCOVERED", index=True)
    status_detail = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    clips = relationship("Clip", back_populates="video", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="video", cascade="all, delete-orphan")
