"""
Ephemeral Storage & Lifecycle Management
=========================================
Manages isolated file workspaces for active conversion requests and enforces a strict
zero-retention privacy policy. Every request is sandboxed in its own UUID-named folder
and automatically destroyed upon delivery or TTL expiry.
"""

import os
import uuid
import time
import shutil
import asyncio
from pathlib import Path
from fastapi import UploadFile
from backend.app.config import TEMP_DIR, FILE_TTL_SECONDS


class TempWorkspace:
    """
    Isolated Workspace Context
    --------------------------
    Encapsulates a single conversion session in a dedicated subfolder (UUID).
    Guarantees concurrency safety by isolating file operations between concurrent users.
    """
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.dir = TEMP_DIR / self.id
        self.dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload_file: UploadFile, filename: str) -> Path:
        """
        Saves an uploaded HTTP multipart stream to disk in 1MB chunks.
        Chunking prevents massive RAM spikes when handling large documents.
        """
        file_path = self.dir / filename
        with open(file_path, "wb") as f:
            while chunk := await upload_file.read(1024 * 1024):  # 1MB buffer
                f.write(chunk)
        return file_path

    def cleanup(self):
        """
        Immediately removes the workspace directory and all intermediate artifacts.
        Ensures complete erasure of user documents from the host machine.
        """
        if self.dir.exists():
            shutil.rmtree(self.dir, ignore_errors=True)


async def delayed_cleanup(workspace: TempWorkspace, delay_seconds: int = 180):
    """
    Deferred Cleanup Hook
    ---------------------
    Runs in the background after returning a FileResponse stream. Allows the client
    ample time (default: 3 minutes) to complete downloading the generated artifact
    before wiping the ephemeral directory.
    """
    await asyncio.sleep(delay_seconds)
    workspace.cleanup()


def cleanup_stale_workspaces(max_age_seconds: int = FILE_TTL_SECONDS):
    """
    Garbage Collection Sweeper
    --------------------------
    Sweeps the temp directory to eliminate orphaned folders created by disconnected
    clients, failed network requests, or server restarts.
    """
    if not TEMP_DIR.exists():
        return
    now = time.time()
    for item in TEMP_DIR.iterdir():
        if item.is_dir():
            try:
                # If directory modification timestamp exceeds TTL, purge it
                if now - item.stat().st_mtime > max_age_seconds:
                    shutil.rmtree(item, ignore_errors=True)
            except Exception:
                pass
