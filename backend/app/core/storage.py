import os
import uuid
import time
import shutil
import asyncio
from pathlib import Path
from fastapi import UploadFile
from backend.app.config import TEMP_DIR, FILE_TTL_SECONDS

class TempWorkspace:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.dir = TEMP_DIR / self.id
        self.dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload_file: UploadFile, filename: str) -> Path:
        """Saves an uploaded stream to an ephemeral file in chunks."""
        file_path = self.dir / filename
        with open(file_path, "wb") as f:
            while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
                f.write(chunk)
        return file_path

    def cleanup(self):
        """Immediately removes the workspace directory and all files inside."""
        if self.dir.exists():
            shutil.rmtree(self.dir, ignore_errors=True)

async def delayed_cleanup(workspace: TempWorkspace, delay_seconds: int = 120):
    """Waits for delay_seconds and purges the workspace to ensure streaming finishes."""
    await asyncio.sleep(delay_seconds)
    workspace.cleanup()

def cleanup_stale_workspaces(max_age_seconds: int = FILE_TTL_SECONDS):
    """Scans the temp directory and deletes workspaces older than max_age_seconds."""
    if not TEMP_DIR.exists():
        return
    now = time.time()
    for item in TEMP_DIR.iterdir():
        if item.is_dir():
            try:
                if now - item.stat().st_mtime > max_age_seconds:
                    shutil.rmtree(item, ignore_errors=True)
            except Exception:
                pass
