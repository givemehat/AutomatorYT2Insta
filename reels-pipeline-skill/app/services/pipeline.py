import datetime
from typing import Dict, Any, List, Optional
from app.config import settings
from app.database import SessionLocal
from app.models.youtube_video import YouTubeVideo
from app.models.clip import Clip
from app.models.processing_job import ProcessingJob
from app.services.youtube import YouTubeService
from app.services.transcription import TranscriptionService
from app.services.ai_strategist import AIStrategistService
from app.services.video_processor import VideoProcessorService
from app.services.quality_control import QualityControlService
from app.services.instagram import InstagramService
from app.services.logger import log_event

class PipelineOrchestrator:
    @classmethod
    def run_full_pipeline_for_video(
        cls,
        video_url_or_id: str,
        force: bool = False,
        reframe_style: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end processing pipeline for a single YouTube video:
        1. Ingest (Metadata, Video Download, 16kHz Audio Extraction)
        2. Transcribe (Zero-quota YouTube subtitle scraper / Gemini / Whisper)
        3. AI Strategist (Editorial analysis, Confidence, Clip boundaries, Copywriting)
        4. Video Processor (Smart Face Tracking / Blur-Stack 9:16 reframe, Subtitles, Loudnorm)
        5. Quality Control (Codec, duration, aspect ratio, text limits)
        6. Publication / Safe-Mode Approval Gate
        """
        clean_id = YouTubeService.extract_video_id(video_url_or_id)
        log_event("INFO", "pipeline", f"=== Launching Repurposing Pipeline for Video: {clean_id} ===")

        with SessionLocal() as db:
            job = ProcessingJob(
                youtube_id=clean_id,
                stage="STARTING",
                status="RUNNING"
            )
            db.add(job)
            db.commit()
            job_id = job.id

        try:
            # 1. Ingestion
            cls._update_job_stage(job_id, "INGESTION")
            video = YouTubeService.ingest_video(clean_id, force=force)

            # 2. Transcription
            cls._update_job_stage(job_id, "TRANSCRIPTION")
            video = TranscriptionService.transcribe_video(clean_id, force=force)

            # 3. AI Strategy
            cls._update_job_stage(job_id, "AI_ANALYSIS")
            ai_decision = AIStrategistService.analyze_video(clean_id, force=force)

            if ai_decision.decision == "SKIP":
                log_event("INFO", "pipeline", f"AI Decision is SKIP for {clean_id}: {ai_decision.reason}")
                with SessionLocal() as db:
                    v = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == clean_id).first()
                    v.processing_status = "SKIPPED"
                    v.status_detail = ai_decision.reason
                    db.commit()
                cls._finish_job(job_id, "COMPLETED", {"decision": "SKIP", "reason": ai_decision.reason})
                return {"status": "SKIPPED", "video_id": clean_id, "reason": ai_decision.reason}

            # 4 & 5. Video Processing & QC
            cls._update_job_stage(job_id, "VIDEO_PROCESSING")
            with SessionLocal() as db:
                clips = db.query(Clip).filter(Clip.youtube_id == clean_id).all()

            processed_clips = []
            for clip in clips:
                # 9:16 Video Rendering with smart face tracking & styled subtitles
                clip_path = VideoProcessorService.reframe_and_render_clip(
                    clip.id,
                    reframe_style=reframe_style or settings.REFRAME_STYLE,
                    force=force
                )
                
                # Pre-flight QC validation
                qc_passed, qc_info = QualityControlService.validate_clip(clip.id)

                # Safe Mode vs Full Auto
                published = False
                if (
                    settings.AUTOMATION_MODE == "FULL_AUTO"
                    and clip.ai_confidence >= settings.AUTO_PUBLISH_THRESHOLD
                    and qc_passed
                ):
                    cls._update_job_stage(job_id, "PUBLISHING")
                    InstagramService.publish_clip(clip.id)
                    published = True
                
                processed_clips.append({
                    "clip_id": clip.id,
                    "title": clip.clip_title,
                    "duration": clip.duration,
                    "qc_passed": qc_passed,
                    "approval_status": "AUTO_PUBLISHED" if published else clip.approval_status
                })

            with SessionLocal() as db:
                v = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == clean_id).first()
                v.processing_status = "PROCESSED"
                db.commit()

            cls._finish_job(job_id, "COMPLETED", {"clips_count": len(processed_clips)})
            log_event("INFO", "pipeline", f"=== Successfully Completed Pipeline for Video: {clean_id} ({len(processed_clips)} clips) ===")

            return {
                "status": "SUCCESS",
                "video_id": clean_id,
                "ai_decision": ai_decision.model_dump(),
                "clips": processed_clips
            }

        except Exception as e:
            log_event("ERROR", "pipeline", f"Pipeline failed for {clean_id}: {e}")
            cls._finish_job(job_id, "FAILED", error_message=str(e))
            with SessionLocal() as db:
                v = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == clean_id).first()
                if v:
                    v.processing_status = "FAILED"
                    v.status_detail = str(e)
                    db.commit()
            raise

    @staticmethod
    def _update_job_stage(job_id: str, stage: str):
        with SessionLocal() as db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.stage = stage
                db.commit()

    @staticmethod
    def _finish_job(job_id: str, status: str, metadata: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None):
        with SessionLocal() as db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.status = status
                job.completed_at = datetime.datetime.now(datetime.timezone.utc)
                if metadata:
                    job.metadata_payload = metadata
                if error_message:
                    job.error_message = error_message
                db.commit()
