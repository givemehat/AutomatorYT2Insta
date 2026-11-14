from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import SessionLocal
from app.models.youtube_video import YouTubeVideo
from app.services.youtube import YouTubeService
from app.services.pipeline import PipelineOrchestrator
from app.services.logger import log_event

scheduler = BackgroundScheduler()

def check_for_new_uploads_job():
    """Periodic daemon that checks YouTube channel for new uploads and triggers pipeline."""
    if not settings.YOUTUBE_CHANNEL_ID:
        return

    log_event("INFO", "scheduler", f"Checking YouTube channel {settings.YOUTUBE_CHANNEL_ID} for new uploads...")
    try:
        videos = YouTubeService.fetch_channel_videos(max_results=10)
        with SessionLocal() as db:
            for v in videos:
                vid_id = v["youtube_id"]
                exists = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == vid_id).first()
                if not exists:
                    log_event("INFO", "scheduler", f"New upload discovered: {v['title']} ({vid_id})! Starting pipeline...")
                    try:
                        PipelineOrchestrator.run_full_pipeline_for_video(vid_id)
                    except Exception as e:
                        log_event("ERROR", "scheduler", f"Auto-process failed for video {vid_id}: {e}")
    except Exception as e:
        log_event("ERROR", "scheduler", f"Periodic YouTube check error: {e}")

def start_scheduler():
    """Starts background upload monitor."""
    if not scheduler.running:
        scheduler.add_job(
            check_for_new_uploads_job,
            trigger=IntervalTrigger(minutes=settings.YOUTUBE_POLL_INTERVAL_MINUTES),
            id="youtube_upload_monitor",
            name="YouTube Channel Upload Monitor",
            replace_existing=True
        )
        scheduler.start()
        log_event("INFO", "scheduler", f"Scheduler active. Polling channel every {settings.YOUTUBE_POLL_INTERVAL_MINUTES}m.")

def shutdown_scheduler():
    """Gracefully shuts down scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        log_event("INFO", "scheduler", "Scheduler shut down.")
