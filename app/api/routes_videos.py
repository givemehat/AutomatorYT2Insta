from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.youtube_video import YouTubeVideo
from app.schemas.youtube import YouTubeVideoResponse, VideoIngestRequest
from app.services.pipeline import PipelineOrchestrator
from app.services.youtube import YouTubeService

router = APIRouter(prefix="/api/videos", tags=["Videos"])

@router.get("", response_model=List[YouTubeVideoResponse])
def list_videos(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Lists all ingested YouTube videos."""
    videos = db.query(YouTubeVideo).order_by(YouTubeVideo.created_at.desc()).offset(skip).limit(limit).all()
    return videos

@router.get("/{youtube_id}", response_model=YouTubeVideoResponse)
def get_video(youtube_id: str, db: Session = Depends(get_db)):
    """Retrieves metadata and processing state of a specific video."""
    clean_id = YouTubeService.extract_video_id(youtube_id)
    video = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == clean_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.post("/ingest")
def ingest_single_video(payload: VideoIngestRequest, background_tasks: BackgroundTasks):
    """Triggers background processing pipeline for a YouTube URL or Video ID."""
    clean_id = YouTubeService.extract_video_id(payload.video_url_or_id)
    background_tasks.add_task(PipelineOrchestrator.run_full_pipeline_for_video, clean_id, payload.force_reprocess)
    return {"status": "QUEUED", "youtube_id": clean_id, "message": "Video processing queued in background."}
