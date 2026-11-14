---
name: yt-to-insta-automation
description: "Autonomous agent skill for running, inspecting, approving, and monitoring the YouTube to Instagram content repurposing pipeline."
version: "2.0.0"
---

# YouTube to Instagram Content Automation Skill

This skill guides an AI agent to autonomously manage, review, and execute the **AutomatorYT2Insta** pipeline.

## Capabilities
1. **Single Video Ingestion**: Repurpose any long-form or short YouTube video into an Instagram Reel.
2. **Channel Batch Migration**: Safely backfill 30-40 videos from a YouTube channel.
3. **Safe-Mode Editorial Review**: Inspect AI decisions, confidence scores, hook segments, and approve or reject clips.
4. **Smart Reframing & Subtitling**: Re-render clips using face-tracking or blur-stack with karaoke subtitles.
5. **Continuous Channel Polling**: Check for new uploads and monitor logs.

## Commands & Workflows

### 1. Ingest a Single Video
```bash
# Ingest by YouTube URL or Video ID
curl -X POST "http://localhost:8000/api/videos/ingest" \
     -H "Content-Type: application/json" \
     -d '{"video_url_or_id": "YOUR_YOUTUBE_URL_OR_ID", "force_reprocess": false}'
```

### 2. Inspect Ingestion & AI Decision
```bash
# Fetch video details
curl -s "http://localhost:8000/api/videos/YOUR_YOUTUBE_ID" | jq .

# Fetch generated clips
curl -s "http://localhost:8000/api/clips?approval_status=PENDING_APPROVAL" | jq .
```

### 3. Approve and Publish to Instagram
```bash
curl -X POST "http://localhost:8000/api/clips/CLIP_ID/approve" \
     -H "Content-Type: application/json" \
     -d '{
       "approved": true,
       "custom_caption": "Custom caption text if desired",
       "custom_hashtags": ["#AI", "#Reels"]
     }'
```

### 4. Batch Migrate Channel
```bash
python scripts/migrate_existing.py --channel-id "YOUR_CHANNEL_ID" --max 40 --delay 5 --reframe-style smart_face_track
```

### 5. Check System Health & Logs
```bash
curl -s "http://localhost:8000/api/system/metrics" | jq .
curl -s "http://localhost:8000/api/system/logs?limit=20" | jq .
```
