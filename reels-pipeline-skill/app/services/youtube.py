import os
import re
import subprocess
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import yt_dlp
import httpx
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import imageio_ffmpeg

from app.config import settings
from app.database import SessionLocal
from app.models.youtube_video import YouTubeVideo
from app.services.logger import log_event

class YouTubeService:
    @staticmethod
    def extract_video_id(url_or_id: str) -> str:
        """Extracts standard 11-character YouTube video ID from various URL patterns or raw ID."""
        cleaned = url_or_id.strip()
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"(?:embed\/|v\/|shorts\/)([0-9A-Za-z_-]{11})",
            r"^([0-9A-Za-z_-]{11})$"
        ]
        for pattern in patterns:
            match = re.search(pattern, cleaned)
            if match:
                return match.group(1)
        return cleaned

    @classmethod
    def get_youtube_client(cls):
        """Builds official Google API client for YouTube Data API v3 if API key is provided."""
        if settings.YOUTUBE_API_KEY:
            try:
                return build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
            except Exception as e:
                log_event("WARNING", "youtube", f"Could not build YouTube API client: {e}")
        return None

    @classmethod
    def scrape_channel_feed_rss(cls, channel_id: str) -> List[Dict[str, Any]]:
        """
        Scrapes YouTube's public Atom/RSS XML feed for a channel.
        Provides zero-quota, instant upload discovery without needing an API key.
        """
        clean_channel = channel_id.strip()
        if clean_channel.startswith("@"):
            url = f"https://www.youtube.com/{clean_channel}/videos"
            return []
        
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={clean_channel}"
        videos = []
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(feed_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "xml")
                    entries = soup.find_all("entry")
                    for entry in entries:
                        v_id_tag = entry.find("yt:videoId")
                        title_tag = entry.find("title")
                        pub_tag = entry.find("published")
                        if v_id_tag and title_tag:
                            v_id = v_id_tag.text.strip()
                            videos.append({
                                "youtube_id": v_id,
                                "title": title_tag.text.strip(),
                                "description": "",
                                "channel_id": clean_channel,
                                "published_at": datetime.datetime.fromisoformat(pub_tag.text.strip().replace("Z", "+00:00")) if pub_tag else None,
                                "thumbnail_url": f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"
                            })
                    if videos:
                        log_event("INFO", "youtube", f"Scraped {len(videos)} videos from YouTube RSS feed for channel {clean_channel}")
        except Exception as e:
            log_event("DEBUG", "youtube", f"RSS feed scrape error: {e}")
        return videos

    @classmethod
    def fetch_channel_videos(cls, channel_id: Optional[str] = None, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves video list from a YouTube channel.
        Hierarchy:
        1. Official YouTube Data API v3 (if API key set)
        2. Channel RSS XML feed (fast & quota-free)
        3. yt-dlp flat playlist extraction (comprehensive fallback)
        """
        target_channel = channel_id or settings.YOUTUBE_CHANNEL_ID
        if not target_channel:
            raise ValueError("No YouTube Channel ID specified in settings or request.")

        log_event("INFO", "youtube", f"Fetching video list for channel: {target_channel}")
        
        # 1. Try YouTube Data API v3
        client = cls.get_youtube_client()
        videos = []

        if client:
            try:
                channel_resp = client.channels().list(
                    part="contentDetails",
                    id=target_channel
                ).execute()
                items = channel_resp.get("items", [])
                if not items:
                    channel_resp = client.channels().list(
                        part="contentDetails",
                        forHandle=target_channel
                    ).execute()
                    items = channel_resp.get("items", [])

                if items:
                    uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
                    next_page_token = None
                    while len(videos) < max_results:
                        playlist_resp = client.playlistItems().list(
                            part="snippet,contentDetails",
                            playlistId=uploads_playlist_id,
                            maxResults=min(50, max_results - len(videos)),
                            pageToken=next_page_token
                        ).execute()

                        for item in playlist_resp.get("items", []):
                            snippet = item["snippet"]
                            v_id = snippet["resourceId"]["videoId"]
                            published_str = snippet.get("publishedAt")
                            published_at = datetime.datetime.fromisoformat(published_str.replace("Z", "+00:00")) if published_str else None
                            thumbs = snippet.get("thumbnails", {})
                            thumb_url = thumbs.get("high", {}).get("url") or thumbs.get("default", {}).get("url")

                            videos.append({
                                "youtube_id": v_id,
                                "title": snippet.get("title"),
                                "description": snippet.get("description"),
                                "published_at": published_at,
                                "channel_id": snippet.get("channelId"),
                                "thumbnail_url": thumb_url
                            })

                        next_page_token = playlist_resp.get("nextPageToken")
                        if not next_page_token:
                            break

                    log_event("INFO", "youtube", f"Retrieved {len(videos)} videos via YouTube Data API v3")
                    return videos
            except Exception as e:
                log_event("WARNING", "youtube", f"YouTube Data API failed, trying web scraping & yt-dlp: {e}")

        # 2. Try RSS Feed scrape
        rss_videos = cls.scrape_channel_feed_rss(target_channel)
        if len(rss_videos) >= max_results:
            return rss_videos[:max_results]

        # 3. yt-dlp flat playlist extraction
        channel_url = f"https://www.youtube.com/channel/{target_channel}" if not target_channel.startswith("http") else target_channel
        if target_channel.startswith("@"):
            channel_url = f"https://www.youtube.com/{target_channel}/videos"

        ydl_opts = {
            "extract_flat": True,
            "skip_download": True,
            "quiet": True,
            "playlistend": max_results,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(channel_url, download=False)
                entries = info.get("entries", [])
                for entry in entries:
                    if entry and "id" in entry:
                        videos.append({
                            "youtube_id": entry["id"],
                            "title": entry.get("title", f"Video {entry['id']}"),
                            "description": entry.get("description", ""),
                            "duration_seconds": entry.get("duration"),
                            "thumbnail_url": entry.get("thumbnail") or f"https://i.ytimg.com/vi/{entry['id']}/hqdefault.jpg",
                            "channel_id": entry.get("channel_id") or target_channel,
                            "published_at": datetime.datetime.now(datetime.timezone.utc)
                        })
            except Exception as e:
                log_event("WARNING", "youtube", f"yt-dlp playlist extraction error: {e}")

        if not videos and rss_videos:
            return rss_videos

        log_event("INFO", "youtube", f"Retrieved {len(videos)} channel videos")
        return videos

    @classmethod
    def fetch_video_metadata(cls, video_id: str) -> Dict[str, Any]:
        """
        Extracts comprehensive metadata, chapters, tags, views, and comments for a video.
        Uses yt-dlp deep info extraction.
        """
        clean_id = cls.extract_video_id(video_id)
        url = f"https://www.youtube.com/watch?v={clean_id}"
        
        ydl_opts = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            upload_date_str = info.get("upload_date")
            published_at = None
            if upload_date_str:
                try:
                    published_at = datetime.datetime.strptime(upload_date_str, "%Y%m%d")
                except Exception:
                    published_at = datetime.datetime.now(datetime.timezone.utc)

            # Extract chapters if present
            raw_chapters = info.get("chapters") or []
            chapters = [
                {"title": c.get("title"), "start_time": c.get("start_time"), "end_time": c.get("end_time")}
                for c in raw_chapters
            ]

            return {
                "youtube_id": clean_id,
                "title": info.get("title", f"Video {clean_id}"),
                "description": info.get("description", ""),
                "duration_seconds": int(info.get("duration", 0)),
                "channel_id": info.get("channel_id", ""),
                "thumbnail_url": info.get("thumbnail") or f"https://i.ytimg.com/vi/{clean_id}/hqdefault.jpg",
                "published_at": published_at,
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "tags": info.get("tags") or [],
                "chapters": chapters
            }

    @classmethod
    def download_video(cls, video_id: str, force: bool = False) -> str:
        """
        Downloads high-definition video using yt-dlp to storage/raw_videos/{video_id}.mp4.
        Returns the absolute local file path.
        """
        clean_id = cls.extract_video_id(video_id)
        out_path = os.path.join(settings.RAW_VIDEOS_DIR, f"{clean_id}.mp4")

        if os.path.exists(out_path) and os.path.getsize(out_path) > 0 and not force:
            log_event("INFO", "youtube", f"Video {clean_id} cached locally at: {out_path}")
            return out_path

        log_event("INFO", "youtube", f"Starting download for video {clean_id}")
        url = f"https://www.youtube.com/watch?v={clean_id}"
        
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": out_path,
            "ffmpeg_location": ffmpeg_exe,
            "quiet": True,
            "no_warnings": True,
            "overwrites": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            raise RuntimeError(f"Failed to download video {clean_id}: File not found or empty.")

        log_event("INFO", "youtube", f"Video download successful: {out_path} ({os.path.getsize(out_path)} bytes)")
        return out_path

    @classmethod
    def extract_audio(cls, video_path: str, video_id: str) -> str:
        """
        Extracts 16kHz mono audio track from video file for speech-to-text processing.
        """
        clean_id = cls.extract_video_id(video_id)
        audio_out_path = os.path.join(settings.AUDIO_DIR, f"{clean_id}.mp3")

        if os.path.exists(audio_out_path) and os.path.getsize(audio_out_path) > 0:
            log_event("INFO", "youtube", f"Audio track already extracted: {audio_out_path}")
            return audio_out_path

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-ar", "16000",
            "-ac", "1",
            "-q:a", "4",
            audio_out_path
        ]

        log_event("INFO", "youtube", f"Extracting 16kHz audio track for {clean_id}")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction failed: {res.stderr}")

        log_event("INFO", "youtube", f"Audio track saved: {audio_out_path}")
        return audio_out_path

    @classmethod
    def ingest_video(cls, url_or_id: str, force: bool = False) -> YouTubeVideo:
        """
        Orchestrates complete ingestion for a YouTube video:
        fetches metadata, saves DB record, downloads MP4, and extracts 16kHz audio.
        """
        clean_id = cls.extract_video_id(url_or_id)
        log_event("INFO", "youtube", f"Ingesting YouTube video {clean_id}")

        with SessionLocal() as db:
            video_record = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == clean_id).first()
            if not video_record:
                meta = cls.fetch_video_metadata(clean_id)
                video_record = YouTubeVideo(
                    youtube_id=clean_id,
                    title=meta.get("title", f"Video {clean_id}"),
                    description=meta.get("description", ""),
                    duration_seconds=meta.get("duration_seconds", 0),
                    channel_id=meta.get("channel_id", ""),
                    thumbnail_url=meta.get("thumbnail_url", ""),
                    published_at=meta.get("published_at"),
                    view_count=meta.get("view_count"),
                    like_count=meta.get("like_count"),
                    tags=meta.get("tags"),
                    chapters=meta.get("chapters"),
                    processing_status="DOWNLOADING"
                )
                db.add(video_record)
                db.commit()
                db.refresh(video_record)
            else:
                video_record.processing_status = "DOWNLOADING"
                db.commit()

        video_path = cls.download_video(clean_id, force=force)
        audio_path = cls.extract_audio(video_path, clean_id)

        with SessionLocal() as db:
            video_record = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == clean_id).first()
            video_record.local_video_path = video_path
            video_record.local_audio_path = audio_path
            video_record.processing_status = "DOWNLOADED"
            db.commit()
            db.refresh(video_record)
            return video_record
