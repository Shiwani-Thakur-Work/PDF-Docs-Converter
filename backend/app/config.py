"""
Configuration Settings
======================
Centralizes environment variables, resource safety boundaries, and operational
thresholds for document processing.
"""

import os
from pathlib import Path

# Base Filesystem Paths
# Calculates the absolute repository root path for consistent relative path resolution
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Ephemeral File Sandbox Directory
# All uploaded and converted documents are stored here in isolated UUID subfolders.
# Can be overridden via the TEMP_CONVERSION_DIR environment variable (e.g., in Docker tmpfs).
TEMP_DIR = Path(os.getenv("TEMP_CONVERSION_DIR", BASE_DIR / "temp_conversions"))

# File Size Safety Limits
# Safeguards server memory and processing pipelines against denial-of-service / huge uploads.
# Default limit is 100 Megabytes per upload.
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Ephemeral Storage Retention Time (TTL)
# Duration (in seconds) before an uncollected or completed conversion folder is deleted.
# Default: 600 seconds (10 minutes).
FILE_TTL_SECONDS = int(os.getenv("FILE_TTL_SECONDS", "600"))

# Ensure the sandbox temporary directory exists at startup
TEMP_DIR.mkdir(parents=True, exist_ok=True)
