# Google Drive Cloud Storage Setup Guide

Meta's Instagram Graph API requires video files to be hosted on a publicly accessible HTTPS endpoint during container creation. While local tunnels (ngrok / Cloudflare Tunnel) work during local development, **Google Drive** provides zero-cost cloud hosting and permanent backup.

---

## 1. Enable Google Drive API
1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. Select or create a project.
3. In the sidebar, go to **APIs & Services &rarr; Library**.
4. Search for **Google Drive API** and click **Enable**.

---

## 2. Create a Service Account
1. Go to **APIs & Services &rarr; Credentials**.
2. Click **Create Credentials &rarr; Service Account**.
3. Name the service account (e.g. `reels-storage-agent`).
4. Click **Create and Continue**, grant the role **Editor**, and complete creation.
5. In the Service Accounts list, click your newly created account, go to the **Keys** tab, and click **Add Key &rarr; Create new key (JSON)**.
6. Save the downloaded JSON file into the project root directory as:
   ```text
   google_drive_credentials.json
   ```

---

## 3. Create & Share Google Drive Folder
1. Open [Google Drive](https://drive.google.com/).
2. Create a folder (e.g. `Instagram_Reels_Automated`).
3. Right-click the folder &rarr; **Share**.
4. Paste the Service Account's email address (e.g. `reels-storage-agent@your-project.iam.gserviceaccount.com`) and grant **Editor** access.
5. Copy the **Folder ID** from the folder URL in your browser:
   `https://drive.google.com/drive/folders/1ABC_XYZ123456789...` -> `1ABC_XYZ123456789...`

---

## 4. Configure .env
Add the following to your `.env` file:
```env
STORAGE_BACKEND=gdrive
GOOGLE_DRIVE_FOLDER_ID=1ABC_XYZ123456789...
```

When a clip is rendered, it is automatically uploaded to your Google Drive folder, assigned public read access, and a direct streaming URL (`https://lh3.googleusercontent.com/d/{file_id}`) is passed to the Meta Instagram Graph API.
