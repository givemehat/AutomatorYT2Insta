from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.clip import Clip
from app.schemas.clip import ClipResponse, ClipApprovalRequest, ClipRerenderRequest
from app.services.video_processor import VideoProcessorService
from app.services.quality_control import QualityControlService
from app.services.instagram import InstagramService

router = APIRouter(prefix="/api/clips", tags=["Clips"])

@router.get("", response_model=List[ClipResponse])
def list_clips(
    approval_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists generated clips with optional filtering by status."""
    query = db.query(Clip)
    if approval_status:
        query = query.filter(Clip.approval_status == approval_status)
    return query.order_by(Clip.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{clip_id}", response_model=ClipResponse)
def get_clip(clip_id: str, db: Session = Depends(get_db)):
    """Retrieves specific clip details."""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip

@router.post("/{clip_id}/approve")
def approve_clip(
    clip_id: str,
    payload: ClipApprovalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Safe Mode: Approves or rejects clip and triggers Instagram publishing."""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    if not payload.approved:
        clip.approval_status = "REJECTED"
        db.commit()
        return {"status": "REJECTED", "clip_id": clip_id}

    if payload.custom_caption:
        clip.caption = payload.custom_caption
    if payload.custom_hashtags is not None:
        clip.hashtags = payload.custom_hashtags

    clip.approval_status = "APPROVED"
    db.commit()

    qc_passed, _ = QualityControlService.validate_clip(clip_id)
    if not qc_passed:
        raise HTTPException(status_code=400, detail="Clip failed Quality Control validation.")

    background_tasks.add_task(InstagramService.publish_clip, clip_id)
    return {"status": "PUBLISHING_QUEUED", "clip_id": clip_id, "message": "Clip approved and queued for Instagram publish."}

@router.post("/{clip_id}/re-render")
def rerender_clip(
    clip_id: str,
    payload: ClipRerenderRequest,
    db: Session = Depends(get_db)
):
    """Re-renders clip with custom reframing style or subtitle preferences."""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    out_path = VideoProcessorService.reframe_and_render_clip(
        clip_id,
        reframe_style=payload.reframe_style,
        burn_subtitles=payload.burn_subtitles,
        force=True
    )
    QualityControlService.validate_clip(clip_id)
    return {"status": "SUCCESS", "clip_id": clip_id, "path": out_path}
