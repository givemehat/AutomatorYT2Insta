import os
import time
import datetime
from typing import Dict, Any, Optional
import httpx

from app.config import settings
from app.database import SessionLocal
from app.models.clip import Clip
from app.models.instagram_post import InstagramPost
from app.services.google_drive import GoogleDriveService
from app.services.logger import log_event

class InstagramService:
    GRAPH_API_VERSION = "v19.0"
    GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

    @classmethod
    def get_public_clip_url(cls, clip_id: str, local_path: Optional[str] = None) -> str:
        """Generates publicly accessible URL for Instagram's servers to download the video."""
        if settings.STORAGE_BACKEND == "gdrive":
            target_path = local_path or os.path.join(settings.CLIPS_DIR, f"{clip_id}.mp4")
            if os.path.exists(target_path):
                gdrive_res = GoogleDriveService.upload_clip_to_drive(target_path, f"clip_{clip_id}.mp4")
                if gdrive_res.get("direct_url"):
                    return gdrive_res["direct_url"]

        return f"{settings.PUBLIC_MEDIA_URL.rstrip('/')}/media/clips/{clip_id}.mp4"

    @classmethod
    def create_reel_container(
        cls,
        video_url: str,
        caption: str,
        share_to_feed: bool = True
    ) -> str:
        """Calls Meta Graph API to initialize a Reel video container."""
        if not settings.INSTAGRAM_ACCOUNT_ID or not settings.META_USER_ACCESS_TOKEN:
            raise ValueError("Instagram Account ID and Meta User Access Token must be configured in .env")

        url = f"{cls.GRAPH_API_BASE}/{settings.INSTAGRAM_ACCOUNT_ID}/media"
        payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true" if share_to_feed else "false",
            "access_token": settings.META_USER_ACCESS_TOKEN
        }

        log_event("INFO", "instagram", f"Creating Instagram Reel container for URL: {video_url}")
        
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, data=payload)
            data = resp.json()

            if resp.status_code != 200 or "id" not in data:
                error_msg = data.get("error", {}).get("message", resp.text)
                log_event("ERROR", "instagram", f"Failed to create Instagram container: {error_msg}")
                raise RuntimeError(f"Instagram Graph API error: {error_msg}")

            container_id = data["id"]
            log_event("INFO", "instagram", f"Reel container created: {container_id}")
            return container_id

    @classmethod
    def wait_for_container_ready(cls, container_id: str, max_wait_seconds: int = 180) -> bool:
        """Polls Instagram Graph API until container status is FINISHED."""
        url = f"{cls.GRAPH_API_BASE}/{container_id}"
        params = {
            "fields": "status_code,status",
            "access_token": settings.META_USER_ACCESS_TOKEN
        }

        start_time = time.time()
        with httpx.Client(timeout=15.0) as client:
            while time.time() - start_time < max_wait_seconds:
                resp = client.get(url, params=params)
                data = resp.json()
                
                status_code = data.get("status_code", "")
                log_event("INFO", "instagram", f"Container {container_id} status: {status_code}")

                if status_code == "FINISHED":
                    return True
                elif status_code in ["ERROR", "EXPIRED"]:
                    raise RuntimeError(f"Instagram container failed: {status_code} ({data.get('status', '')})")

                time.sleep(5)

        raise TimeoutError(f"Timed out waiting for Instagram container {container_id} to finish.")

    @classmethod
    def publish_container(cls, container_id: str) -> str:
        """Publishes the uploaded video container to Instagram."""
        url = f"{cls.GRAPH_API_BASE}/{settings.INSTAGRAM_ACCOUNT_ID}/media_publish"
        payload = {
            "creation_id": container_id,
            "access_token": settings.META_USER_ACCESS_TOKEN
        }

        log_event("INFO", "instagram", f"Publishing container {container_id} to Instagram")

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, data=payload)
            data = resp.json()

            if resp.status_code != 200 or "id" not in data:
                error_msg = data.get("error", {}).get("message", resp.text)
                raise RuntimeError(f"Failed to publish Instagram container: {error_msg}")

            media_id = data["id"]
            log_event("INFO", "instagram", f"Published to Instagram! Media ID: {media_id}")
            return media_id

    @classmethod
    def fetch_media_permalink(cls, media_id: str) -> Optional[str]:
        """Fetches the public instagram.com permalink for the published post."""
        url = f"{cls.GRAPH_API_BASE}/{media_id}"
        params = {
            "fields": "permalink",
            "access_token": settings.META_USER_ACCESS_TOKEN
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    return resp.json().get("permalink")
        except Exception as e:
            log_event("WARNING", "instagram", f"Could not fetch permalink for {media_id}: {e}")
        return None

    @classmethod
    def publish_clip(cls, clip_id: str) -> InstagramPost:
        """
        Coordinates publishing a QC-passed clip to Instagram.
        Falls back to local simulation mode if Meta credentials are not configured in .env.
        """
        with SessionLocal() as db:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            if not clip:
                raise ValueError(f"Clip {clip_id} not found.")

            if clip.qc_status != "PASS":
                raise ValueError(f"Clip {clip_id} has not passed Quality Control checks.")

            post = db.query(InstagramPost).filter(InstagramPost.clip_id == clip_id).first()
            if not post:
                post = InstagramPost(
                    clip_id=clip_id,
                    publication_status="UPLOADING"
                )
                db.add(post)
                db.commit()
                db.refresh(post)

        public_url = cls.get_public_clip_url(clip_id, clip.local_clip_path)
        caption_text = clip.caption or ""
        if clip.hashtags:
            caption_text += "\n\n" + " ".join(clip.hashtags)

        # Simulation mode if credentials not configured
        if not settings.INSTAGRAM_ACCOUNT_ID or not settings.META_USER_ACCESS_TOKEN:
            simulated_media_id = f"sim_ig_{int(time.time())}"
            simulated_permalink = f"https://instagram.com/reel/{simulated_media_id}"
            log_event("INFO", "instagram", f"[SIMULATION] Meta credentials not configured. Simulating publish: {simulated_permalink}")

            with SessionLocal() as db:
                post = db.query(InstagramPost).filter(InstagramPost.clip_id == clip_id).first()
                post.ig_container_id = f"sim_container_{int(time.time())}"
                post.ig_media_id = simulated_media_id
                post.ig_permalink = simulated_permalink
                post.publication_status = "PUBLISHED"
                post.published_at = datetime.datetime.now(datetime.timezone.utc)
                
                clip = db.query(Clip).filter(Clip.id == clip_id).first()
                clip.approval_status = "APPROVED"
                db.commit()
                db.refresh(post)
                return post

        try:
            container_id = cls.create_reel_container(public_url, caption_text)
            with SessionLocal() as db:
                post = db.query(InstagramPost).filter(InstagramPost.clip_id == clip_id).first()
                post.ig_container_id = container_id
                post.publication_status = "PROCESSING"
                db.commit()

            cls.wait_for_container_ready(container_id)
            media_id = cls.publish_container(container_id)
            permalink = cls.fetch_media_permalink(media_id) or f"https://instagram.com/reel/{media_id}"

            with SessionLocal() as db:
                post = db.query(InstagramPost).filter(InstagramPost.clip_id == clip_id).first()
                post.ig_media_id = media_id
                post.ig_permalink = permalink
                post.publication_status = "PUBLISHED"
                post.published_at = datetime.datetime.now(datetime.timezone.utc)
                
                clip = db.query(Clip).filter(Clip.id == clip_id).first()
                clip.approval_status = "APPROVED"
                db.commit()
                db.refresh(post)
                return post

        except Exception as e:
            with SessionLocal() as db:
                post = db.query(InstagramPost).filter(InstagramPost.clip_id == clip_id).first()
                if post:
                    post.publication_status = "FAILED"
                    post.error_details = str(e)
                    db.commit()
            log_event("ERROR", "instagram", f"Publishing failed for clip {clip_id}: {e}")
            raise
