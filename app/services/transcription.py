import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import yt_dlp
import httpx

from app.config import settings
from app.database import SessionLocal
from app.models.youtube_video import YouTubeVideo
from app.services.logger import log_event

class TranscriptionService:
    @classmethod
    def extract_youtube_subtitles(cls, youtube_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Attempts to scrape existing YouTube subtitles or automatic captions.
        Fast, zero-cost, and accurate without third-party API dependencies.
        """
        url = f"https://www.youtube.com/watch?v={youtube_id}"
        ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "en-US", "en-GB", "hi", "auto"],
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                subtitles = info.get("subtitles") or info.get("automatic_captions") or {}
                
                lang_key = next((k for k in ["en", "en-US", "en-GB", "hi"] if k in subtitles), None)
                if not lang_key and subtitles:
                    lang_key = list(subtitles.keys())[0]

                if lang_key and subtitles[lang_key]:
                    formats = subtitles[lang_key]
                    json3_entry = next((f for f in formats if f.get("ext") == "json3"), None)
                    if json3_entry and "url" in json3_entry:
                        resp = httpx.get(json3_entry["url"], timeout=10.0)
                        if resp.status_code == 200:
                            data = resp.json()
                            events = data.get("events", [])
                            segments = []
                            for ev in events:
                                t_start = ev.get("tStartMs", 0) / 1000.0
                                d_duration = ev.get("dDurationMs", 0) / 1000.0
                                seg_segs = ev.get("segs", [])
                                text_content = "".join([s.get("utf8", "") for s in seg_segs]).strip()
                                if text_content and text_content != "\n":
                                    segments.append({
                                        "start": round(t_start, 2),
                                        "end": round(t_start + d_duration, 2),
                                        "text": text_content.replace("\n", " ")
                                    })
                            if segments:
                                log_event("INFO", "transcription", f"Extracted {len(segments)} caption segments from YouTube for {youtube_id}")
                                return segments
        except Exception as e:
            log_event("DEBUG", "transcription", f"Direct YouTube captions extraction skipped: {e}")
        return None

    @classmethod
    def transcribe_with_gemini(cls, audio_path: str) -> List[Dict[str, Any]]:
        """Transcribes audio using Google Gemini multimodal capabilities."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        log_event("INFO", "transcription", f"Uploading audio to Gemini: {audio_path}")
        
        uploaded_file = client.files.upload(file=audio_path)
        prompt = """
        Please transcribe this audio accurately with word/sentence timestamps.
        Return a JSON array of objects in this exact format:
        [
          {
            "start": 0.0,
            "end": 4.5,
            "text": "Exact spoken words"
          }
        ]
        Make sure timestamps are numbers representing seconds. Output ONLY valid JSON.
        """

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        raw_text = response.text.strip()
        data = json.loads(raw_text)
        return data

    @classmethod
    def transcribe_with_openai(cls, audio_path: str) -> List[Dict[str, Any]]:
        """Transcribes audio using OpenAI Whisper API with segment timestamps."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured.")

        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        log_event("INFO", "transcription", f"Transcribing audio with OpenAI Whisper API: {audio_path}")
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
            
        segments = []
        if hasattr(transcript, "segments") and transcript.segments:
            for s in transcript.segments:
                segments.append({
                    "start": round(s["start"], 2),
                    "end": round(s["end"], 2),
                    "text": s["text"].strip()
                })
        else:
            segments.append({
                "start": 0.0,
                "end": 0.0,
                "text": getattr(transcript, "text", "")
            })
        return segments

    @classmethod
    def transcribe_video(cls, youtube_id: str, force: bool = False) -> YouTubeVideo:
        """
        Coordinates full transcription pipeline:
        1. Checks database cache.
        2. Tries direct YouTube subtitle scraping (instant & quota-free).
        3. Falls back to Gemini / OpenAI Whisper API if keys exist.
        4. Heuristic fallback from description/title.
        """
        with SessionLocal() as db:
            video = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == youtube_id).first()
            if not video:
                raise ValueError(f"Video {youtube_id} not found in database.")
            
            if video.transcript_timestamps and not force:
                log_event("INFO", "transcription", f"Transcript for {youtube_id} already cached.")
                return video

            video.processing_status = "TRANSCRIBING"
            db.commit()

        # Step 1: Direct YouTube Subtitle Scraping
        segments = cls.extract_youtube_subtitles(youtube_id)

        # Step 2: Fallback to AI engines
        if not segments:
            audio_path = video.local_audio_path or os.path.join(settings.AUDIO_DIR, f"{youtube_id}.mp3")
            if os.path.exists(audio_path):
                if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
                    try:
                        segments = cls.transcribe_with_gemini(audio_path)
                    except Exception as e:
                        log_event("WARNING", "transcription", f"Gemini transcription failed: {e}")

                if not segments and settings.OPENAI_API_KEY:
                    try:
                        segments = cls.transcribe_with_openai(audio_path)
                    except Exception as e:
                        log_event("WARNING", "transcription", f"OpenAI transcription failed: {e}")

        # Step 3: Heuristic Fallback
        if not segments:
            log_event("INFO", "transcription", f"Using description and title fallback for {youtube_id}")
            dur = float(video.duration_seconds or 60.0)
            segments = [{
                "start": 0.0,
                "end": dur,
                "text": video.description or video.title
            }]

        full_raw_transcript = " ".join([seg["text"] for seg in segments])

        with SessionLocal() as db:
            video = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == youtube_id).first()
            video.transcript_raw = full_raw_transcript
            video.transcript_timestamps = segments
            video.processing_status = "TRANSCRIBED"
            db.commit()
            db.refresh(video)
            log_event("INFO", "transcription", f"Transcription completed for {youtube_id} ({len(segments)} segments)")
            return video
