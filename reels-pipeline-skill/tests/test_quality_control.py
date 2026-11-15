import pytest
from app.database import init_db, SessionLocal
from app.models.youtube_video import YouTubeVideo
from app.models.clip import Clip
from app.services.quality_control import QualityControlService

def test_quality_control_validation():
    init_db()
    with SessionLocal() as db:
        v = YouTubeVideo(youtube_id="qc_unit_vid", title="QC Unit Test Video")
        db.merge(v)
        
        # Test clip with too short duration (<15s)
        clip_short = Clip(
            id="test_clip_short",
            youtube_id="qc_unit_vid",
            clip_title="Too Short Clip",
            start_time=0.0,
            end_time=8.0,
            duration=8.0,
            decision_type="POST_SHORT_CLIP",
            ai_confidence=0.88,
            caption="Valid Caption for Test",
            hashtags=["#Testing"]
        )
        db.merge(clip_short)
        db.commit()

    is_passed, checks = QualityControlService.validate_clip("test_clip_short")
    assert not is_passed
    assert any("shorter than minimum" in issue for issue in checks["issues"])
