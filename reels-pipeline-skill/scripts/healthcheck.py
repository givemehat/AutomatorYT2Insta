#!/usr/bin/env python3
"""
Diagnostic utility to verify runtime prerequisites:
- Python version (>=3.10)
- FFmpeg binary availability
- OpenCV face detection capabilities
- Write permissions for storage directories
- Configuration and optional API credentials status
"""

import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

def check_environment():
    print("=" * 60)
    print(" AutomatorYT2Insta — System Diagnostic Healthcheck")
    print("=" * 60)

    # 1. Python Version
    py_ver = sys.version_info
    print(f"[+] Python Version: {py_ver.major}.{py_ver.minor}.{py_ver.micro} -> ", end="")
    if py_ver >= (3, 10):
        print("OK")
    else:
        print("FAIL (Requires Python 3.10+)")

    # 2. FFmpeg Executable
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"[+] FFmpeg Binary: {ffmpeg_exe} -> OK")
    except Exception as e:
        print(f"[-] FFmpeg Binary Error: {e}")

    # 3. OpenCV
    try:
        import cv2
        print(f"[+] OpenCV Version: {cv2.__version__} -> OK")
    except Exception as e:
        print(f"[-] OpenCV Import Error: {e}")

    # 4. Storage Directories
    from app.config import settings
    settings.ensure_directories()
    all_writable = True
    for d in [settings.STORAGE_DIR, settings.RAW_VIDEOS_DIR, settings.AUDIO_DIR, settings.CLIPS_DIR, settings.SUBTITLES_DIR]:
        if not os.access(d, os.W_OK):
            print(f"[-] Directory Not Writable: {d}")
            all_writable = False
    if all_writable:
        print(f"[+] Storage Cache Directories ({settings.STORAGE_DIR}): Writable -> OK")

    # 5. Database Initialization
    try:
        from app.database import init_db
        init_db()
        print(f"[+] Database Connection ({settings.DATABASE_URL}): Initialized -> OK")
    except Exception as e:
        print(f"[-] Database Error: {e}")

    # 6. Optional Credentials Status
    print("\n--- Optional Service Credentials ---")
    print(f"• LLM Provider: {settings.LLM_PROVIDER} (Key configured: {bool(settings.GEMINI_API_KEY or settings.OPENAI_API_KEY)})")
    print(f"• YouTube Data API Key: {'Configured' if settings.YOUTUBE_API_KEY else 'Not configured (RSS/Web scraper fallback active)'}")
    print(f"• Instagram Meta Token: {'Configured' if settings.META_USER_ACCESS_TOKEN else 'Not configured (Simulation mode active)'}")
    print(f"• Cloud Storage: {settings.STORAGE_BACKEND}")
    print("=" * 60)
    print("Healthcheck Complete!")

if __name__ == "__main__":
    check_environment()
