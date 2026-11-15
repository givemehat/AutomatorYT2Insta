from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class YouTubeVideoBase(BaseModel):
    youtube_id: str
    title: str
    description: Optional[str] = None
    duration_seconds: Optional[int] = None
    published_at: Optional[datetime] = None
    channel_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    tags: Optional[List[str]] = None
    chapters: Optional[List[Dict[str, Any]]] = None

class YouTubeVideoCreate(YouTubeVideoBase):
    pass

class YouTubeVideoResponse(YouTubeVideoBase):
    model_config = ConfigDict(from_attributes=True)

    processing_status: str
    status_detail: Optional[str] = None
    local_video_path: Optional[str] = None
    local_audio_path: Optional[str] = None
    transcript_raw: Optional[str] = None
    transcript_timestamps: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

class VideoIngestRequest(BaseModel):
    video_url_or_id: str
    force_reprocess: bool = False
