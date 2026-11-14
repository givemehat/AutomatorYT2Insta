from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class ClipBase(BaseModel):
    youtube_id: str
    clip_title: str
    start_time: float
    end_time: float
    duration: float
    decision_type: str
    ai_confidence: float
    ai_reasoning: Optional[str] = None
    content_type: Optional[str] = None
    virality_score: Optional[float] = 0.85
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None

class ClipCreate(ClipBase):
    local_clip_path: Optional[str] = None

class ClipResponse(ClipBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    local_clip_path: Optional[str] = None
    subtitle_path: Optional[str] = None
    cloud_url: Optional[str] = None
    qc_status: str
    qc_details: Optional[Dict[str, Any]] = None
    approval_status: str
    created_at: datetime
    updated_at: datetime

class ClipApprovalRequest(BaseModel):
    approved: bool
    custom_caption: Optional[str] = None
    custom_hashtags: Optional[List[str]] = None

class ClipRerenderRequest(BaseModel):
    reframe_style: Optional[str] = "smart_face_track"
    burn_subtitles: Optional[bool] = True
    subtitle_style: Optional[str] = "karaoke_highlight"
