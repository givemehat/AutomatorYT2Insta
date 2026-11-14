from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class ClipBoundary(BaseModel):
    start_seconds: float = Field(..., description="Start timestamp in seconds from the source video")
    end_seconds: float = Field(..., description="End timestamp in seconds from the source video")
    hook_sentence: Optional[str] = Field(None, description="The opening hook statement that grabs attention")
    summary: Optional[str] = Field(None, description="Brief summary of this specific segment")
    virality_score: Optional[float] = Field(0.85, ge=0.0, le=1.0, description="Estimated engagement score (0.0 - 1.0)")

class AIDecisionOutput(BaseModel):
    video_id: str = Field(..., description="The YouTube video ID being analyzed")
    decision: Literal[
        "POST_FULL_REEL",
        "POST_SHORT_CLIP",
        "POST_MULTIPLE_CLIPS",
        "SKIP",
        "REQUIRE_REVIEW"
    ] = Field(..., description="Strategic decision on how to repurpose this content")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0 reflecting suitability and quality"
    )
    reason: str = Field(..., description="In-depth editorial reasoning behind the decision")
    content_type: str = Field(..., description="Category: educational, tutorial, hot_take, entertainment, story, etc.")
    
    # Clip details
    recommended_duration: Optional[float] = Field(None, description="Total recommended clip duration in seconds")
    clips: List[ClipBoundary] = Field(default_factory=list, description="List of 1 or more extracted clips")
    
    # Instagram Copywriting
    title: str = Field(..., description="Rewritten Instagram-optimized headline or hook title")
    caption: str = Field(..., description="Instagram-native caption with hook, value points, and CTA")
    hashtags: List[str] = Field(default_factory=list, description="Content-specific hashtags (5-15 hashtags)")
    
    # Format and safety
    recommended_format: Literal["9:16", "1:1", "16:9"] = "9:16"
    requires_review: bool = Field(False, description="Flag if human moderation/review is strongly recommended")
