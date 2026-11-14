from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.instagram_post import InstagramPost
from app.schemas.instagram import InstagramPostResponse, InstagramPublishRequest
from app.services.instagram import InstagramService

router = APIRouter(prefix="/api/posts", tags=["Instagram Posts"])

@router.get("", response_model=List[InstagramPostResponse])
def list_posts(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Lists all published Instagram post records."""
    posts = db.query(InstagramPost).order_by(InstagramPost.created_at.desc()).offset(skip).limit(limit).all()
    return posts

@router.post("/publish")
def publish_clip_post(payload: InstagramPublishRequest, background_tasks: BackgroundTasks):
    """Directly queues Instagram publishing for a clip."""
    background_tasks.add_task(InstagramService.publish_clip, payload.clip_id)
    return {"status": "QUEUED", "clip_id": payload.clip_id, "message": "Publishing job started."}
