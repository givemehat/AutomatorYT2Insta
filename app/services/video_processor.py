import os
import subprocess
from pathlib import Path
from typing import Optional, Literal, Tuple, List, Dict, Any
import cv2
import imageio_ffmpeg

from app.config import settings
from app.database import SessionLocal
from app.models.clip import Clip
from app.models.youtube_video import YouTubeVideo
from app.services.subtitles import SubtitleService
from app.services.logger import log_event

class VideoProcessorService:
    @staticmethod
    def get_ffmpeg_binary() -> str:
        """Returns valid FFmpeg executable path from imageio_ffmpeg."""
        return imageio_ffmpeg.get_ffmpeg_exe()

    @classmethod
    def detect_speaker_horizontal_center(
        cls,
        video_path: str,
        start_seconds: float,
        duration: float,
        sample_interval: float = 1.0
    ) -> float:
        """
        Calculates speaker horizontal center (0.0 to 1.0) using computer vision.
        Compatible across OpenCV 4.x and OpenCV 5.x.
        Falls back gracefully to center 0.50 if detection is not available.
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return 0.5

            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            src_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920.0
            
            detected_centers = []
            current_t = start_seconds
            end_t = start_seconds + duration

            # Check if CascadeClassifier is available (OpenCV 4.x)
            face_cascade = None
            if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data"):
                cascade_file = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                if os.path.exists(cascade_file):
                    face_cascade = cv2.CascadeClassifier(cascade_file)

            while current_t < end_t:
                frame_num = int(current_t * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                if face_cascade:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
                    if len(faces) > 0:
                        largest_face = max(faces, key=lambda f: f[2] * f[3])
                        fx, fy, fw, fh = largest_face
                        detected_centers.append((fx + fw / 2.0) / src_width)

                current_t += sample_interval

            cap.release()

            if detected_centers:
                avg_center = sum(detected_centers) / len(detected_centers)
                log_event("INFO", "video_processor", f"Smart Tracking detected speaker center at {avg_center:.2f}")
                return max(0.2, min(0.8, avg_center))
        except Exception as e:
            log_event("WARNING", "video_processor", f"Speaker tracking error, using default center: {e}")

        return 0.5

    @classmethod
    def generate_reframe_filter(
        cls,
        reframe_style: str,
        video_path: str,
        start_t: float,
        duration: float,
        subtitle_file: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """
        Builds FFmpeg filter complex for vertical 9:16:
        1. 'smart_face_track': Crops 9:16 centered on speaker's horizontal position.
        2. 'blur_stack': Blurred 9:16 background with sharp 16:9 foreground overlay.
        3. 'center_crop': Standard center 9:16 crop.
        """
        if reframe_style == "smart_face_track":
            center_ratio = cls.detect_speaker_horizontal_center(video_path, start_t, duration)
            filter_str = (
                f"[0:v]crop='min(in_w, in_h*9/16)':'in_h':'max(0, min(in_w - in_h*9/16, in_w*{center_ratio:.3f} - (in_h*9/16)/2))':0,"
                "scale=1080:1920,setsar=1[v]"
            )
        elif reframe_style == "center_crop":
            filter_str = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,setsar=1[v]"
            )
        else:
            # blur_stack
            filter_str = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[bg];"
                "[0:v]scale=1080:-2[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v]"
            )

        if subtitle_file and os.path.exists(subtitle_file):
            escaped_sub = subtitle_file.replace("\\", "/").replace(":", "\\:")
            filter_str = filter_str.replace("[v]", "[base];")
            filter_str += f"[base]subtitles='{escaped_sub}'[v]"

        return filter_str, ["[v]"]

    @classmethod
    def reframe_and_render_clip(
        cls,
        clip_id: str,
        reframe_style: Optional[str] = None,
        burn_subtitles: Optional[bool] = None,
        force: bool = False
    ) -> str:
        """
        Renders a 9:16 Instagram Reel from source video with:
        - Trim boundaries [start_time, end_time].
        - Reframe mode: smart face tracking, blur stack, or center crop.
        - Subtitles: ASS karaoke-style highlights burned in.
        - Audio: EBU R128 loudness normalization (-14 LUFS).
        - Encoding: H.264 / AAC with +faststart.
        """
        with SessionLocal() as db:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            if not clip:
                raise ValueError(f"Clip {clip_id} not found.")

            video = db.query(YouTubeVideo).filter(YouTubeVideo.youtube_id == clip.youtube_id).first()
            if not video or not video.local_video_path or not os.path.exists(video.local_video_path):
                raise FileNotFoundError(f"Source video for clip {clip_id} missing on disk.")

            output_clip_path = os.path.join(settings.CLIPS_DIR, f"{clip.id}.mp4")

            if os.path.exists(output_clip_path) and os.path.getsize(output_clip_path) > 0 and not force:
                log_event("INFO", "video_processor", f"Clip {clip_id} cached at: {output_clip_path}")
                clip.local_clip_path = output_clip_path
                db.commit()
                return output_clip_path

        style = reframe_style or settings.REFRAME_STYLE
        should_sub = burn_subtitles if burn_subtitles is not None else settings.ENABLE_SUBTITLES

        start_t = clip.start_time
        duration = clip.duration
        source_path = video.local_video_path

        subtitle_file = None
        if should_sub and video.transcript_timestamps:
            clip_segs = []
            for seg in video.transcript_timestamps:
                s_start = seg.get("start", 0.0)
                s_end = seg.get("end", 0.0)
                if s_end > start_t and s_start < (start_t + duration):
                    rel_start = max(0.0, s_start - start_t)
                    rel_end = min(duration, s_end - start_t)
                    if rel_end > rel_start:
                        clip_segs.append({
                            "start": rel_start,
                            "end": rel_end,
                            "text": seg.get("text", "")
                        })
            if clip_segs:
                sub_path = os.path.join(settings.SUBTITLES_DIR, f"{clip.id}.ass")
                SubtitleService.generate_ass_subtitles(clip_segs, sub_path, style_preset=settings.SUBTITLE_STYLE)
                subtitle_file = sub_path

        log_event("INFO", "video_processor", f"Rendering clip {clip_id} (duration={duration:.1f}s, style={style}, subtitles={bool(subtitle_file)})")

        filter_complex, map_nodes = cls.generate_reframe_filter(
            style, source_path, start_t, duration, subtitle_file=subtitle_file
        )

        ffmpeg_exe = cls.get_ffmpeg_binary()
        cmd = [
            ffmpeg_exe,
            "-y",
            "-ss", str(start_t),
            "-t", str(duration),
            "-i", source_path,
            "-filter_complex", filter_complex,
            "-map", map_nodes[0],
            "-map", "0:a?",
            "-af", "loudnorm=I=-14:LRA=11:TP=-1.5",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-movflags", "+faststart",
            output_clip_path
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            log_event("WARNING", "video_processor", f"FFmpeg filter complex failed, using safe fallback: {res.stderr}")
            fallback_cmd = [
                ffmpeg_exe,
                "-y",
                "-ss", str(start_t),
                "-t", str(duration),
                "-i", source_path,
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-pix_fmt", "yuv420p",
                output_clip_path
            ]
            subprocess.run(fallback_cmd, check=True)

        with SessionLocal() as db:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            clip.local_clip_path = output_clip_path
            clip.subtitle_path = subtitle_file
            db.commit()

        log_event("INFO", "video_processor", f"Rendered 9:16 clip saved: {output_clip_path} ({os.path.getsize(output_clip_path)} bytes)")
        return output_clip_path
