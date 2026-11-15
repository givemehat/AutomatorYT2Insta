# Configuration & Environment Variables Reference

All settings can be configured via environment variables or a `.env` file placed in the project root directory.

---

## 1. Core Application Settings

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | string | `development` | Environment mode (`development` or `production`) |
| `DEBUG` | boolean | `True` | Enables verbose debug outputs and auto-reload |
| `SECRET_KEY` | string | random string | Cryptographic secret for signing sessions |
| `BASE_URL` | string | `http://localhost:8000` | Application root web URL |
| `PUBLIC_MEDIA_URL` | string | `http://localhost:8000` | Publicly reachable HTTPS URL (ngrok, Cloudflare Tunnel, or domain) used by Meta to ingest video containers |

---

## 2. Automation & Pipeline Guardrails

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `AUTOMATION_MODE` | `SAFE` \| `FULL_AUTO` | `SAFE` | In `SAFE` mode, clips wait in the review queue for 1-click human approval. In `FULL_AUTO`, clips meeting the threshold and passing QC are published immediately. |
| `AUTO_PUBLISH_THRESHOLD` | float | `0.85` | Minimum AI confidence score required for autonomous publishing (0.0 to 1.0) |
| `MAX_REEL_DURATION_SECONDS` | int | `90` | Maximum duration allowed for an extracted Reel clip |
| `MIN_CLIP_DURATION_SECONDS` | int | `15` | Minimum duration allowed for an extracted clip |

---

## 3. Video Reframing & Subtitling Settings

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `REFRAME_STYLE` | `smart_face_track` \| `blur_stack` \| `center_crop` | `smart_face_track` | `smart_face_track`: uses OpenCV computer vision to detect the speaker's face and centers the 9:16 crop.<br>`blur_stack`: scales 16:9 foreground over blurred 9:16 background.<br>`center_crop`: direct center crop. |
| `ENABLE_SUBTITLES` | boolean | `True` | Burn styled subtitles into output video |
| `SUBTITLE_STYLE` | `karaoke_highlight` \| `classic_yellow` \| `bold_clean` | `karaoke_highlight` | Subtitle typography and highlight animation preset |

---

## 4. Ingestion & YouTube Settings

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `YOUTUBE_API_KEY` | string | `None` | Google Cloud YouTube Data API v3 key. If omitted, the system seamlessly falls back to public RSS XML and web scraping. |
| `YOUTUBE_CHANNEL_ID` | string | `None` | Target YouTube Channel ID or handle (e.g. `UC...` or `@yourhandle`) for continuous polling |
| `YOUTUBE_POLL_INTERVAL_MINUTES` | int | `30` | Interval in minutes between automated checks for new video uploads |

---

## 5. AI Strategist & LLM Provider

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `LLM_PROVIDER` | `gemini` \| `openai` | `gemini` | Primary AI provider for content strategy |
| `GEMINI_API_KEY` | string | `None` | Google Gemini API key |
| `GEMINI_MODEL` | string | `gemini-2.5-flash` | Gemini model name |
| `OPENAI_API_KEY` | string | `None` | OpenAI API key |
| `OPENAI_MODEL` | string | `gpt-4o-mini` | OpenAI chat completion model name |

*(Note: If no LLM API keys are configured, the system uses an intelligent offline heuristic fallback engine, ensuring zero downtime and fully offline testability).*

---

## 6. Meta Instagram Graph API Settings

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `INSTAGRAM_ACCOUNT_ID` | string | `None` | Instagram Business/Creator Account ID |
| `FACEBOOK_PAGE_ID` | string | `None` | Connected Facebook Page ID |
| `META_APP_ID` | string | `None` | Meta Developer App ID |
| `META_APP_SECRET` | string | `None` | Meta Developer App Secret |
| `META_USER_ACCESS_TOKEN` | string | `None` | 60-day Long-Lived Meta User Access Token |

*(Note: If Instagram credentials are not provided, publishing automatically switches to **Simulation Mode** allowing full local end-to-end testing).*

---

## 7. Cloud Storage Settings

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `STORAGE_BACKEND` | `local` \| `gdrive` \| `s3` | `local` | Storage location for rendered media |
| `GOOGLE_DRIVE_FOLDER_ID` | string | `None` | Google Drive folder ID (requires `google_drive_credentials.json` service account key in root) |
| `AWS_ACCESS_KEY_ID` | string | `None` | S3 / Cloudflare R2 access key |
| `AWS_SECRET_ACCESS_KEY` | string | `None` | S3 / Cloudflare R2 secret key |
| `AWS_BUCKET_NAME` | string | `None` | S3 / R2 bucket name |
| `AWS_REGION` | string | `us-east-1` | S3 bucket region |
