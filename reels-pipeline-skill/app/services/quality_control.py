import os
import json
import subprocess
from typing import Dict, Any, Tuple
import imageio_ffmpeg

from app.config import settings
from app.database import SessionLocal
from app.models.clip import Clip
from app.services.logger import log_event

class QualityControlService:
    @classmethod
    def inspect_video_stream(cls, file_path: str) -> Dict[str, Any]:
        """Probes technical stream properties using FFmpeg."""
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [ffmpeg_exe, "-i", file_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stderr = res.stderr

        return {
            "has_video": "Video:" in stderr,
            "has_audio": "Audio:" in stderr,
            "is_h264": "h264" in stderr.lower(),
            "is_aac": "aac" in stderr.lower(),
            "raw_info": stderr
        }

    @classmethod
    def validate_clip(cls, clip_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Runs comprehensive pre-flight QC checks on rendered clip before publishing.
        1. Media file existence and size.
        2. Audio and Video stream codecs.
        3. Duration constraints.
        4. Instagram caption character limit (<= 2,200).
        5. Hashtag limit (<= 30).
        """
        with SessionLocal() as db:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            if not clip:
                raise ValueError(f"Clip {clip_id} not found.")

        issues = []
        checks = {}

        # 1. Media File Verification
        clip_path = clip.local_clip_path
        if not clip_path or not os.path.exists(clip_path):
            issues.append(f"Media file missing: {clip_path}")
            checks["file_exists"] = False
        else:
            file_size_bytes = os.path.getsize(clip_path)
            checks["file_exists"] = True
            checks["file_size_mb"] = round(file_size_bytes / (1024 * 1024), 2)
            if file_size_bytes < 10000:
                issues.append("File size too small (<10KB).")

            stream_info = cls.inspect_video_stream(clip_path)
            checks["has_video"] = stream_info["has_video"]
            checks["has_audio"] = stream_info["has_audio"]
            if not stream_info["has_video"]:
                issues.append("Video stream missing.")

        # 2. Duration Check
        checks["duration_seconds"] = clip.duration
        if clip.duration < settings.MIN_CLIP_DURATION_SECONDS:
            issues.append(f"Clip duration ({clip.duration:.1f}s) shorter than minimum allowed ({settings.MIN_CLIP_DURATION_SECONDS}s).")
        if clip.duration > settings.MAX_REEL_DURATION_SECONDS:
            issues.append(f"Clip duration ({clip.duration:.1f}s) exceeds maximum allowed ({settings.MAX_REEL_DURATION_SECONDS}s).")

        # 3. Caption Checks
        caption = clip.caption or ""
        checks["caption_length"] = len(caption)
        if len(caption) > 2200:
            issues.append(f"Caption exceeds 2200 character limit ({len(caption)} chars).")
        if len(caption.strip()) == 0:
            issues.append("Caption is completely empty.")

        # 4. Hashtag Checks
        hashtags = clip.hashtags or []
        checks["hashtag_count"] = len(hashtags)
        if len(hashtags) > 30:
            issues.append(f"Hashtag count ({len(hashtags)}) exceeds 30.")

        is_passed = len(issues) == 0
        checks["issues"] = issues
        checks["passed"] = is_passed

        with SessionLocal() as db:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            clip.qc_status = "PASS" if is_passed else "FAIL"
            clip.qc_details = checks
            db.commit()

        if is_passed:
            log_event("INFO", "qc", f"Quality control PASSED for clip {clip_id}")
        else:
            log_event("WARNING", "qc", f"Quality control FAILED for clip {clip_id}: {'; '.join(issues)}")

        return is_passed, checks
