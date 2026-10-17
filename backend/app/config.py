import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMP_DIR = Path(os.getenv("TEMP_CONVERSION_DIR", BASE_DIR / "temp_conversions"))

# File Limits
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Cleanup settings
FILE_TTL_SECONDS = int(os.getenv("FILE_TTL_SECONDS", "600"))  # 10 minutes

# Ensure Temp Directory Exists
TEMP_DIR.mkdir(parents=True, exist_ok=True)
