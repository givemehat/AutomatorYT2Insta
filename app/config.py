import os
from pathlib import Path
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "super-secret-key-change-in-production-automator-yt2insta"
    BASE_URL: str = "http://localhost:8000"
    PUBLIC_MEDIA_URL: str = "http://localhost:8000"

    # Operating Mode: SAFE (Manual approval via dashboard) vs FULL_AUTO (Autonomous publishing above threshold)
    AUTOMATION_MODE: Literal["SAFE", "FULL_AUTO"] = "SAFE"
    AUTO_PUBLISH_THRESHOLD: float = 0.85
    MAX_REEL_DURATION_SECONDS: int = 90
    MIN_CLIP_DURATION_SECONDS: int = 15

    # Video Processing & Computer Vision Reframing
    REFRAME_STYLE: Literal["smart_face_track", "blur_stack", "center_crop"] = "smart_face_track"
    ENABLE_SUBTITLES: bool = True
    SUBTITLE_STYLE: Literal["karaoke_highlight", "classic_yellow", "bold_clean"] = "karaoke_highlight"

    # Storage Paths
    STORAGE_DIR: str = str(BASE_DIR / "storage")
    RAW_VIDEOS_DIR: str = str(BASE_DIR / "storage" / "raw_videos")
    AUDIO_DIR: str = str(BASE_DIR / "storage" / "audio")
    CLIPS_DIR: str = str(BASE_DIR / "storage" / "clips")
    SUBTITLES_DIR: str = str(BASE_DIR / "storage" / "subtitles")
    TEMP_DIR: str = str(BASE_DIR / "storage" / "temp")

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/automator.db"

    # YouTube Data API v3 & Ingestion
    YOUTUBE_API_KEY: Optional[str] = None
    YOUTUBE_CHANNEL_ID: Optional[str] = None
    YOUTUBE_POLL_INTERVAL_MINUTES: int = 30

    # AI Strategic Decision Engine
    LLM_PROVIDER: Literal["gemini", "openai"] = "gemini"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Transcription Engine
    TRANSCRIPTION_ENGINE: Literal["gemini", "whisper_api", "faster_whisper", "youtube_scrape"] = "gemini"
    WHISPER_MODEL_SIZE: str = "base"

    # Instagram Graph API
    INSTAGRAM_ACCOUNT_ID: Optional[str] = None
    FACEBOOK_PAGE_ID: Optional[str] = None
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    META_USER_ACCESS_TOKEN: Optional[str] = None

    # Cloud Storage (Google Drive / S3 / Local)
    STORAGE_BACKEND: Literal["local", "gdrive", "s3"] = "local"
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_BUCKET_NAME: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    def ensure_directories(self) -> None:
        for p in [
            self.STORAGE_DIR,
            self.RAW_VIDEOS_DIR,
            self.AUDIO_DIR,
            self.CLIPS_DIR,
            self.SUBTITLES_DIR,
            self.TEMP_DIR,
        ]:
            os.makedirs(p, exist_ok=True)

settings = Settings()
settings.ensure_directories()
