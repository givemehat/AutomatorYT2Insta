from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class InstagramPostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    clip_id: str
    ig_container_id: Optional[str] = None
    ig_media_id: Optional[str] = None
    ig_permalink: Optional[str] = None
    publication_status: str
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    error_details: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class InstagramPublishRequest(BaseModel):
    clip_id: str
    schedule_time: Optional[datetime] = None
