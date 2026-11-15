---
name: reels-pipeline-automation
description: "Autonomous AI-powered pipeline to repurpose long-form and short YouTube videos into high-retention 9:16 Instagram Reels with smart face-tracking, karaoke subtitles, quality control, and Meta Graph API publishing."
version: "1.0.0"
author: "givemehat"
license: "MIT"
tags:
  - youtube
  - instagram
  - reels
  - video-processing
  - ai-automation
  - opencv
  - ffmpeg
---

# YouTube &rarr; Instagram Reels Automation Skill

## Overview & When to Use

Use this skill when an autonomous AI agent needs to repurpose YouTube content (either single videos or whole channel catalogs) into production-ready vertical (9:16) Instagram Reels.

The skill provides an end-to-end automated pipeline covering:
1. **Metadata & Video Ingestion**: Downloading 1080p video and extracting 16kHz audio using `yt-dlp` or YouTube Data API v3 with public RSS web scraping fallbacks.
2. **Speech Transcription**: Zero-quota direct caption scraping or Gemini 2.5 Flash / Whisper API transcription with word-level timestamps.
3. **AI Content Strategy**: Analyzing hook strength (first 3 seconds), standalone narrative coherence, pacing, and retention to produce structured repurposing decisions (`POST_FULL_REEL`, `POST_SHORT_CLIP`, `POST_MULTIPLE_CLIPS`, `SKIP`, `REQUIRE_REVIEW`).
4. **Smart 9:16 Video Reframing**: Using OpenCV computer vision to detect speaker face coordinates and center the vertical crop smoothly, or applying cinematic blurred-background stacking.
5. **Karaoke Subtitling & Audio Mastering**: Burning in animated ASS/SRT subtitles with highlighted active words and normalizing audio to EBU R128 (-14 LUFS) broadcasting standards.
6. **Quality Control & Publishing**: Pre-flight validation against Instagram format limits, followed by automated Meta Graph API container creation and publication (with optional Google Drive cloud streaming).

---

## Required Inputs & Configuration

### Primary Inputs
- `video_url_or_id`: YouTube video URL (standard watch, shortened `youtu.be`, `shorts/`, embed) or raw 11-character video ID.
- `channel_id`: (For batch processing) YouTube Channel ID or handle (e.g. `UC...` or `@channelname`).

### Configuration Settings (`.env` or Environment Variables)
- `AUTOMATION_MODE`:
  - `SAFE` (Default): Clips are staged in the web dashboard for human review and 1-click approval.
  - `FULL_AUTO`: Autonomous publishing if AI confidence score &ge; `AUTO_PUBLISH_THRESHOLD` and Quality Control passes.
- `AUTO_PUBLISH_THRESHOLD`: Float between `0.0` and `1.0` (default: `0.85`).
- `REFRAME_STYLE`:
  - `smart_face_track`: Centers 9:16 vertical crop on the speaker's face using OpenCV.
  - `blur_stack`: Crisp 16:9 foreground on top of Gaussian-blurred 9:16 background.
  - `center_crop`: Static center 9:16 crop.
- `ENABLE_SUBTITLES`: Boolean (`True`/`False`, default: `True`).
- `SUBTITLE_STYLE`: `karaoke_highlight`, `classic_yellow`, or `bold_clean`.
- `STORAGE_BACKEND`: `local` (default), `gdrive` (Google Drive), or `s3`.
- `LLM_PROVIDER`: `gemini` (default) or `openai` (offline heuristic fallback active if keys omitted).
- `META_USER_ACCESS_TOKEN` & `INSTAGRAM_ACCOUNT_ID`: Meta Graph API credentials (operates in simulation mode if omitted).

---

## Expected Outputs

1. **Structured Decision JSON**:
   - `decision`: `POST_FULL_REEL`, `POST_SHORT_CLIP`, `POST_MULTIPLE_CLIPS`, `SKIP`, or `REQUIRE_REVIEW`.
   - `confidence`: Confidence score (0.0 to 1.0).
   - `virality_score`: Predicted engagement potential.
   - `reason`: In-depth editorial justification.
   - `clips`: Array of `{start_seconds, end_seconds, hook_sentence, summary}`.
   - `caption`: Instagram-native copy (headline hook, bullets, CTA, hashtags).
2. **Rendered Video**:
   - 1080x1920 MP4 file (H.264 video, AAC audio, 30fps, EBU R128 -14 LUFS audio, faststart enabled) stored in `storage/clips/{clip_id}.mp4`.
3. **Subtitles**:
   - Formatted `.ass` and `.srt` subtitle files stored in `storage/subtitles/{clip_id}.ass`.
4. **Quality Control Report**:
   - Technical validation pass/fail with verified video stream, audio stream, duration (15s–90s), and character limits.
5. **Publishing Status**:
   - In Full Auto mode: Meta Graph API container ID, media ID, and live Instagram permalink.
   - In Safe Mode: `PENDING_APPROVAL` status visible on the Web Dashboard (`http://localhost:8000`).

---

## Step-by-Step Agent Execution Workflows

### Workflow A: Single Video Processing (CLI)
When tasked with processing a single YouTube URL directly from the terminal:

1. **Verify Environment**:
   ```bash
   python scripts/healthcheck.py
   ```
2. **Run Pipeline**:
   ```bash
   python scripts/run_pipeline.py --video "https://www.youtube.com/watch?v=VIDEO_ID" --style smart_face_track
   ```
3. **Check Output**:
   The script prints the complete JSON summary, clip paths, and status.

---

### Workflow B: Single Video Processing via REST API
When integrating with an existing server or external web service:

1. **Start Server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. **Dispatch Ingestion Request**:
   ```bash
   curl -X POST "http://localhost:8000/api/videos/ingest" \
        -H "Content-Type: application/json" \
        -d '{"video_url_or_id": "https://www.youtube.com/watch?v=VIDEO_ID", "force_reprocess": false}'
   ```
3. **Poll Video State**:
   ```bash
   curl -s "http://localhost:8000/api/videos/VIDEO_ID"
   ```
4. **List Generated Clips**:
   ```bash
   curl -s "http://localhost:8000/api/clips?approval_status=PENDING_APPROVAL"
   ```
5. **Approve and Publish**:
   ```bash
   curl -X POST "http://localhost:8000/api/clips/CLIP_ID/approve" \
        -H "Content-Type: application/json" \
        -d '{"approved": true, "custom_caption": "Optional updated caption", "custom_hashtags": ["#AI", "#Reels"]}'
   ```

---

### Workflow C: Batch Channel Migration (30–40 Videos)
When tasked with backfilling an entire YouTube channel:

1. **Run Migration Script**:
   ```bash
   python scripts/migrate_existing.py --channel-id "CHANNEL_ID_OR_HANDLE" --max 40 --delay 5 --reframe-style smart_face_track
   ```
2. **Monitor Progress**:
   The interactive terminal display shows a live progress bar, processed count, skipped count (duplicates or AI SKIP decisions), and failures.

---

### Workflow D: Web Dashboard Operation (Human-in-the-Loop)
1. Start the server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Open `http://localhost:8000` in any web browser.
3. Review staged clips in the **Clips Review Queue**:
   - Preview the 9:16 video in the embedded player.
   - Inspect AI confidence score and virality metrics.
   - Edit caption or hashtags inline.
   - Click **Approve & Post** to publish or **Reject** to dismiss.

---

## Error Handling & Edge Case Management

| Failure Condition | Automatic Resolution |
| :--- | :--- |
| **No Google API Key** | Automatically falls back to public RSS XML feed and `yt-dlp` web extraction. |
| **No LLM API Key (Offline)** | Seamlessly activates deterministic heuristic analysis engine. |
| **No Meta Access Token** | Runs in local simulation mode (generates simulated container IDs and permalinks). |
| **Face Tracking Fails (No face in frame)** | Automatically centers video crop (0.50 ratio) and logs fallback. |
| **Complex FFmpeg Filter Error** | Automatically falls back to standard center crop filter without crashing. |
| **Duplicate Video Encountered** | Skips re-downloading and re-transcribing unless `--force` is passed. |
| **Clip Fails QC Checks** | Blocks publishing, logs specific failure reasons, and marks status as `FAIL`. |

---

## Technical Dependencies & Requirements
- **Python**: 3.10 or higher.
- **FFmpeg**: Automatically provided via `imageio-ffmpeg` (or system FFmpeg if installed).
- **Core Libraries**: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `yt-dlp`, `opencv-python-headless`, `google-genai`, `openai`, `apscheduler`, `rich`.
