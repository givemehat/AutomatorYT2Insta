import uuid
import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON
from app.database import Base

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    level = Column(String(16), default="INFO", index=True)  # INFO, WARNING, ERROR, CRITICAL
    source = Column(String(64), nullable=False, index=True)  # youtube, whisper, ai_strategist, ffmpeg, instagram, qc
    message = Column(Text, nullable=False)
    context_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)
