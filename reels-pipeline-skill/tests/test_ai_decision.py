import pytest
from app.schemas.ai_decision import AIDecisionOutput, ClipBoundary
from app.models.youtube_video import YouTubeVideo
from app.services.ai_strategist import AIStrategistService

def test_ai_decision_schema_validation():
    valid_data = {
        "video_id": "test_123",
        "decision": "POST_SHORT_CLIP",
        "confidence": 0.94,
        "reason": "Strong standalone value in opening hook segment",
        "content_type": "educational",
        "recommended_duration": 42.0,
        "clips": [
            {
                "start_seconds": 15.0,
                "end_seconds": 57.0,
                "hook_sentence": "Here is the one concept you need to know today.",
                "summary": "Core breakthrough explained clearly",
                "virality_score": 0.91
            }
        ],
        "title": "The One Concept You Need to Know 💡",
        "caption": "Breakdown of the core concept in under 60 seconds.\n\n📌 Save this for later!",
        "hashtags": ["#AI", "#Tech", "#LearnFast"],
        "recommended_format": "9:16",
        "requires_review": False
    }
    decision = AIDecisionOutput(**valid_data)
    assert decision.decision == "POST_SHORT_CLIP"
    assert decision.confidence == 0.94
    assert len(decision.clips) == 1
    assert decision.clips[0].virality_score == 0.91

def test_heuristic_fallback_with_chapters():
    video = YouTubeVideo(
        youtube_id="demo_ch_123",
        title="Complete Guide to Quantum Physics",
        duration_seconds=600,
        chapters=[
            {"title": "Intro", "start_time": 0.0, "end_time": 30.0},
            {"title": "Qubits and Superposition", "start_time": 30.0, "end_time": 80.0}
        ],
        transcript_timestamps=[
            {"start": 30.0, "end": 45.0, "text": "Superposition allows qubits to explore multiple pathways."},
            {"start": 45.0, "end": 75.0, "text": "This exponential state space gives quantum computing its power."}
        ]
    )
    decision = AIStrategistService._evaluate_with_heuristic_fallback(video)
    assert decision.video_id == "demo_ch_123"
    assert decision.decision == "POST_SHORT_CLIP"
    assert decision.clips[0].start_seconds == 30.0
    assert len(decision.hashtags) > 0
