import os
from typing import Optional, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.config import settings
from app.services.logger import log_event

class GoogleDriveService:
    SCOPES = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    @classmethod
    def get_drive_service(cls):
        """
        Initializes Google Drive API service using service account JSON credentials
        if google_drive_credentials.json is placed in root directory.
        """
        creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "google_drive_credentials.json")
        
        if os.path.exists(creds_path):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    creds_path, scopes=cls.SCOPES
                )
                return build("drive", "v3", credentials=creds)
            except Exception as e:
                log_event("WARNING", "gdrive", f"Failed to initialize Google Drive service: {e}")
        return None

    @classmethod
    def upload_clip_to_drive(
        cls,
        local_file_path: str,
        filename: str,
        folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Uploads a rendered 9:16 clip to Google Drive, sets public link permissions,
        and returns the Direct Download URL and View URL.
        """
        service = cls.get_drive_service()
        if not service:
            log_event("WARNING", "gdrive", "google_drive_credentials.json not found. Skipping Google Drive upload.")
            return {}

        target_folder = folder_id or settings.GOOGLE_DRIVE_FOLDER_ID
        
        file_metadata = {
            "name": filename,
            "parents": [target_folder] if target_folder else []
        }
        
        media = MediaFileUpload(
            local_file_path,
            mimetype="video/mp4",
            resumable=True
        )

        log_event("INFO", "gdrive", f"Uploading {filename} to Google Drive...")
        
        drive_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink, webContentLink"
        ).execute()

        file_id = drive_file.get("id")

        try:
            service.permissions().create(
                fileId=file_id,
                body={"role": "reader", "type": "anyone"},
                fields="id"
            ).execute()
        except Exception as e:
            log_event("WARNING", "gdrive", f"Failed to set reader permission on Drive file {file_id}: {e}")

        direct_url = f"https://lh3.googleusercontent.com/d/{file_id}"
        log_event("INFO", "gdrive", f"Uploaded to Google Drive! File ID: {file_id}")
        
        return {
            "file_id": file_id,
            "web_view_link": drive_file.get("webViewLink"),
            "direct_url": direct_url
        }
