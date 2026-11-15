# FastAPI REST API Reference

The service runs by default at `http://localhost:8000`. Interactive OpenAPI documentation is accessible at `http://localhost:8000/docs`.

---

## 1. Video Ingestion Endpoints

### Ingest Video
`POST /api/videos/ingest`

Queues a background job to download, extract audio, transcribe, analyze, reframe, and generate clips.

**Request Body:**
```json
{
  "video_url_or_id": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "force_reprocess": false
}
```

**Response (200 OK):**
```json
{
  "status": "QUEUED",
  "youtube_id": "dQw4w9WgXcQ",
  "message": "Video processing queued in background."
}
```

### List Ingested Videos
`GET /api/videos?skip=0&limit=50`

Returns paginated list of ingested YouTube videos and their statuses (`DOWNLOADING`, `DOWNLOADED`, `TRANSCRIBED`, `DECISION_MADE`, `PROCESSED`, `SKIPPED`, `FAILED`).

### Get Single Video Details
`GET /api/videos/{youtube_id}`

Returns video metadata, full raw transcript, and timestamped segments.

---

## 2. Clip Management Endpoints

### List Clips
`GET /api/clips?approval_status=PENDING_APPROVAL&skip=0&limit=50`

Filter options for `approval_status`:
- `PENDING_APPROVAL`: Safe-Mode review queue.
- `APPROVED`: Approved and queued/posted.
- `REJECTED`: Editorial rejection.
- `AUTO_APPROVED`: Published autonomously in Full-Auto mode.

### Get Single Clip
`GET /api/clips/{clip_id}`

Returns clip boundaries (`start_time`, `end_time`), decision type, virality score, caption, hashtags, QC status, and local media path.

### Approve / Reject Clip
`POST /api/clips/{clip_id}/approve`

**Request Body:**
```json
{
  "approved": true,
  "custom_caption": "Updated caption text if desired",
  "custom_hashtags": ["#AI", "#Reels", "#Tech"]
}
```

**Response (200 OK):**
```json
{
  "status": "PUBLISHING_QUEUED",
  "clip_id": "c1f7b09e-...",
  "message": "Clip approved and queued for Instagram publish."
}
```

### Re-render Clip
`POST /api/clips/{clip_id}/re-render`

Re-renders the clip with a different visual crop or subtitle style.

**Request Body:**
```json
{
  "reframe_style": "blur_stack",
  "burn_subtitles": true,
  "subtitle_style": "karaoke_highlight"
}
```

---

## 3. Direct Publishing Endpoints

### Publish Clip
`POST /api/posts/publish`

Directly triggers the Instagram Graph API publishing routine.

**Request Body:**
```json
{
  "clip_id": "c1f7b09e-..."
}
```

### List Published Posts
`GET /api/posts?skip=0&limit=50`

Lists all published Instagram post records, container IDs, media IDs, and permalinks.

---

## 4. System & Observability Endpoints

### Operational Metrics
`GET /api/system/metrics`

Returns counts of total videos, processed, pending approvals, published posts, and active configuration.

### System Audit Logs
`GET /api/system/logs?limit=50`

Returns chronological system audit log entries.

### Trigger Channel Scan
`POST /api/system/trigger-scan`

Immediately polls the configured YouTube channel for new uploads in a background worker thread.
