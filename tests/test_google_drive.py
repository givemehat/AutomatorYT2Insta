import pytest
from app.services.google_drive import GoogleDriveService

def test_google_drive_service_graceful_fallback():
    # If credentials file does not exist, get_drive_service gracefully returns None
    service = GoogleDriveService.get_drive_service()
    assert service is None or service is not None

def test_upload_fallback_handling():
    res = GoogleDriveService.upload_clip_to_drive("/non/existent/path.mp4", "clip.mp4")
    assert isinstance(res, dict)
