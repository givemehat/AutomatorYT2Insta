import os
import subprocess
import pytest
import imageio_ffmpeg
from app.database import init_db, SessionLocal
from app.models.youtube_video import YouTubeVideo
from app.models.clip import Clip
from app.services.video_processor import VideoProcessorService
from app.services.quality_control import QualityControlService
from app.config import settings

def test_video_processor_render_and_qc(tmp_path):
    init_db()
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    # 1. Generate a small synthetic 16:9 video (1280x720, 20 seconds)
    test_src_video = os.path.join(settings.RAW_VIDEOS_DIR, "synthetic_test.mp4")
    gen_cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=20:size=1280x720:rate=30",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=20",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        test_src_video
    ]
    subprocess.run(gen_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # 2. Add records in DB with timestamps for subtitles
    with SessionLocal() as db:
        v = YouTubeVideo(
            youtube_id="synthetic_test",
            title="Synthetic Face Test Video",
            local_video_path=test_src_video,
            duration_seconds=20,
            transcript_timestamps=[
                {"start": 2.0, "end": 8.0, "text": "This is synthetic test subtitle speech."},
                {"start": 8.0, "end": 18.0, "text": "Testing smart reframe and audio normalization."}
            ]
        )
        db.merge(v)

        c = Clip(
            id="synthetic_clip_01",
            youtube_id="synthetic_test",
            clip_title="Synthetic Clip 01",
            start_time=2.0,
            end_time=18.0,
            duration=16.0,
            decision_type="POST_SHORT_CLIP",
            ai_confidence=0.95,
            caption="High quality synthetic clip with subtitles and audio normalization.",
            hashtags=["#Tech", "#Testing"]
        )
        db.merge(c)
        db.commit()

    # 3. Test horizontal center detection
    center_x = VideoProcessorService.detect_speaker_horizontal_center(test_src_video, 2.0, 16.0)
    assert 0.0 <= center_x <= 1.0

    # 4. Render 9:16 Clip using smart_face_track with subtitles
    rendered_path = VideoProcessorService.reframe_and_render_clip(
        "synthetic_clip_01",
        reframe_style="blur_stack",
        burn_subtitles=True,
        force=True
    )
    assert os.path.exists(rendered_path)
    assert os.path.getsize(rendered_path) > 0

    # 5. Run Quality Control
    passed, checks = QualityControlService.validate_clip("synthetic_clip_01")
    assert passed, f"QC failed with checks: {checks}"
    assert checks["file_exists"] is True
    assert checks["has_video"] is True
    assert checks["has_audio"] is True
    assert checks["duration_seconds"] == 16.0
