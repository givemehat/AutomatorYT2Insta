#!/usr/bin/env python3
"""
CLI entrypoint to run the Reels automation pipeline on a single YouTube video.
Usage:
    python scripts/run_pipeline.py --video "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    python scripts/run_pipeline.py --video "dQw4w9WgXcQ" --style blur_stack --force
"""

import sys
import argparse
import json
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database import init_db
from app.services.pipeline import PipelineOrchestrator
from app.services.youtube import YouTubeService

def main():
    parser = argparse.ArgumentParser(description="Process a single YouTube video into Instagram Reel(s).")
    parser.add_argument("--video", "-v", required=True, help="YouTube video URL or 11-character video ID")
    parser.add_argument("--style", "-s", default="smart_face_track", choices=["smart_face_track", "blur_stack", "center_crop"], help="Reframe mode")
    parser.add_argument("--force", "-f", action="store_true", help="Force re-download and re-processing even if cached")
    args = parser.parse_args()

    # Ensure tables exist
    init_db()

    video_id = YouTubeService.extract_video_id(args.video)
    print(f"[*] Starting pipeline for video: {video_id} (Reframe: {args.style})")

    try:
        result = PipelineOrchestrator.run_full_pipeline_for_video(
            video_url_or_id=video_id,
            force=args.force,
            reframe_style=args.style
        )
        print("\n[+] Pipeline Completed Successfully!")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n[-] Pipeline Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
