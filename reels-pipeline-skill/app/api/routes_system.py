import threading
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.youtube_video import YouTubeVideo
from app.models.clip import Clip
from app.models.instagram_post import InstagramPost
from app.models.system_log import SystemLog
from app.services.scheduler import check_for_new_uploads_job

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/metrics")
def get_system_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns real-time operational metrics for dashboard."""
    total_videos = db.query(YouTubeVideo).count()
    processed_videos = db.query(YouTubeVideo).filter(YouTubeVideo.processing_status == "PROCESSED").count()
    failed_videos = db.query(YouTubeVideo).filter(YouTubeVideo.processing_status == "FAILED").count()
    skipped_videos = db.query(YouTubeVideo).filter(YouTubeVideo.processing_status == "SKIPPED").count()

    total_clips = db.query(Clip).count()
    pending_approvals = db.query(Clip).filter(Clip.approval_status == "PENDING_APPROVAL").count()
    qc_passed_clips = db.query(Clip).filter(Clip.qc_status == "PASS").count()

    published_posts = db.query(InstagramPost).filter(InstagramPost.publication_status == "PUBLISHED").count()

    return {
        "videos": {
            "total": total_videos,
            "processed": processed_videos,
            "failed": failed_videos,
            "skipped": skipped_videos
        },
        "clips": {
            "total": total_clips,
            "pending_approval": pending_approvals,
            "qc_passed": qc_passed_clips
        },
        "instagram": {
            "published": published_posts
        },
        "config": {
            "mode": settings.AUTOMATION_MODE,
            "threshold": settings.AUTO_PUBLISH_THRESHOLD,
            "reframe_style": settings.REFRAME_STYLE,
            "subtitles_enabled": settings.ENABLE_SUBTITLES,
            "storage_backend": settings.STORAGE_BACKEND,
            "llm_provider": settings.LLM_PROVIDER,
            "youtube_channel": settings.YOUTUBE_CHANNEL_ID or "Not configured",
            "instagram_account": settings.INSTAGRAM_ACCOUNT_ID or "Not configured"
        }
    }

@router.get("/logs")
def get_system_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Returns recent system logs for monitoring."""
    logs = db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "level": l.level,
            "source": l.source,
            "message": l.message,
            "created_at": l.created_at.isoformat() if l.created_at else None
        }
        for l in logs
    ]

@router.post("/trigger-scan")
def trigger_channel_scan():
    """Manually triggers an immediate YouTube channel upload check in a worker thread."""
    threading.Thread(target=check_for_new_uploads_job, daemon=True).start()
    return {"status": "TRIGGERED", "message": "Channel scan launched in background."}
