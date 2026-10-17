# Implementation Plan & Technical Roadmap

> **Document:** Implementation Guide & Step-by-Step Execution Plan  
> **Target Audience:** Developers, DevOps Engineers  
> **Status:** Implementation Ready  

---

## 1. Directory & Codebase Structure

To maintain a clean, maintainable, and modular repository, the project adopts the following structure:

```
PDF-Docs-Converter/
├── docs/
│   ├── context.md               # Vision, core capabilities, and quality mandates
│   ├── architecture.md          # Technical design, pipelines, and subsystems
│   └── implementation.md        # This implementation guide and roadmap
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app initialization, CORS, static mounting
│   │   ├── config.py            # App settings (max file size, temp directory, TTL)
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes_convert.py # PDF<->DOCX conversion endpoints
│   │   │   ├── routes_tools.py   # Compress, merge, split endpoints
│   │   │   └── routes_health.py  # Liveness & readiness probes
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── validator.py     # Magic-number & file validation
│   │   │   ├── storage.py       # Ephemeral temp file manager & auto-cleanup
│   │   │   └── exceptions.py    # Standardized error definitions
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── pdf_to_docx.py   # High-fidelity layout conversion (pdf2docx)
│   │       ├── docx_to_pdf.py   # Headless LibreOffice rendering engine
│   │       ├── pdf_compress.py  # PyMuPDF stream optimization
│   │       └── pdf_ops.py       # Merge and split utilities
├── frontend/
│   ├── index.html               # Semantic HTML5 single-page application
│   ├── css/
│   │   └── style.css            # Minimalist, modern dark/glassmorphism design
│   └── js/
│       ├── app.js               # UI controller, drag & drop, state management
│       └── api.js               # Fetch client for conversion API & downloads
├── tests/
│   ├── test_validators.py       # Magic-number and size checks
│   ├── test_pdf_to_docx.py      # Conversion fidelity tests
│   └── test_docx_to_pdf.py      # LibreOffice headless execution tests
├── Dockerfile                   # Multi-stage production container with LibreOffice & Fonts
├── docker-compose.yml           # Local one-command development & testing
├── requirements.txt             # Python backend dependencies
├── .env.example                 # Config template
├── .gitignore                   # Clean ignore rules
└── README.md                    # Project landing documentation
```

---

## 2. Dependencies & Prerequisites

### 2.1 Backend Dependencies (`requirements.txt`)
```txt
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
python-multipart>=0.0.9
pydantic>=2.6.0
pdf2docx>=0.5.8
PyMuPDF>=1.23.26
pypdf>=4.1.0
python-docx>=1.1.0
aiofiles>=23.2.1
```

### 2.2 System-Level Dependencies (for DOCX ➔ PDF)
- **LibreOffice:** Headless document rendering engine (`soffice`).
  - *Ubuntu/Debian:* `apt-get install -y libreoffice --no-install-recommends`
  - *macOS:* `brew install --cask libreoffice`
  - *Windows:* Installed via official installer or Chocolatey (`choco install libreoffice-fresh`).
- **Standard Open Fonts:** Required to prevent font substitution during DOCX ➔ PDF rendering:
  - `fonts-liberation`, `fonts-dejavu`, `fonts-freefont-ttf`

---

## 3. Core Engine Implementations

### 3.1 PDF to DOCX Service (`backend/app/services/pdf_to_docx.py`)
```python
import os
import asyncio
from pdf2docx import Converter
from backend.app.core.exceptions import ConversionError

async def convert_pdf_to_docx(input_path: str, output_path: str) -> str:
    """
    Converts a PDF file into a Microsoft Word (.docx) document.
    Executes in a thread pool to avoid blocking the async event loop.
    """
    def _run_conversion():
        try:
            cv = Converter(input_path)
            # multi_processing=True accelerates processing for multi-page documents
            cv.convert(output_path, start=0, end=None)
            cv.close()
        except Exception as e:
            raise ConversionError(f"PDF to DOCX conversion failed: {str(e)}")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_conversion)
    
    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise ConversionError("Output file was not generated or is empty.")
        
    return output_path
```

### 3.2 DOCX to PDF Service (`backend/app/services/docx_to_pdf.py`)
```python
import os
import asyncio
import subprocess
from backend.app.core.exceptions import ConversionError

async def convert_docx_to_pdf(input_path: str, output_dir: str) -> str:
    """
    Converts DOCX/DOC to PDF using headless LibreOffice.
    Guarantees cross-platform layout preservation.
    """
    cmd = [
        "soffice",
        "--headless",
        "--convert-to", "pdf:writer_pdf_Export",
        "--outdir", output_dir,
        input_path
    ]
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60.0)
        
        if proc.returncode != 0:
            raise ConversionError(f"LibreOffice failed with code {proc.returncode}: {stderr.decode()}")
            
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_pdf = os.path.join(output_dir, f"{base_name}.pdf")
        
        if not os.path.exists(output_pdf):
            raise ConversionError("Expected PDF output was not produced.")
            
        return output_pdf
    except asyncio.TimeoutError:
        raise ConversionError("Document conversion timed out (> 60 seconds).")
```

### 3.3 Ephemeral Storage Manager & Auto-Garbage Collector
```python
import os
import time
import shutil
import asyncio
from pathlib import Path

TEMP_ROOT = Path("/tmp/pdf_docs_converter")

async def schedule_auto_cleanup(folder_path: str, delay_seconds: int = 600):
    """Purges a conversion workspace after delay_seconds (10 minutes)."""
    await asyncio.sleep(delay_seconds)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path, ignore_errors=True)

def run_garbage_collector(max_age_seconds: int = 600):
    """Scans and clears stale folders during startup and scheduled cron checks."""
    if not TEMP_ROOT.exists():
        return
    now = time.time()
    for item in TEMP_ROOT.iterdir():
        if item.is_dir() and (now - item.stat().st_mtime > max_age_seconds):
            shutil.rmtree(item, ignore_errors=True)
```

---

## 4. API Specification & Endpoints

| Method | Endpoint | Payload | Response | Description |
|---|---|---|---|---|
| `POST` | `/api/convert/pdf-to-docx` | `multipart/form-data` (`file`) | File Stream (`.docx`) | Converts input PDF to an editable DOCX file. |
| `POST` | `/api/convert/docx-to-pdf` | `multipart/form-data` (`file`) | File Stream (`.pdf`) | Converts input DOCX to a high-fidelity PDF file. |
| `POST` | `/api/tools/compress-pdf` | `multipart/form-data` (`file`, `level`) | File Stream (`.pdf`) | Compresses PDF streams and resamples images. |
| `POST` | `/api/tools/merge-pdf` | `multipart/form-data` (`files[]`) | File Stream (`.pdf`) | Merges two or more PDFs into a unified document. |
| `POST` | `/api/tools/split-pdf` | `multipart/form-data` (`file`, `pages`) | File Stream / ZIP | Splits specified pages or generates single-page PDFs. |
| `GET` | `/api/health` | None | `{"status": "ok", "engines": {...}}` | Reports server status and LibreOffice availability. |

---

## 5. UI/UX Implementation Details

The frontend is intentionally designed to be **minimal, responsive, and distraction-free**:

1. **Dropzone Component:**
   - Visual states: Default, Hover/Dragover, Processing, Success, Error.
   - Immediate client-side format detection (`.pdf`, `.docx`, `.doc`).
2. **Auto-Target Suggestion:**
   - Dropping a `.pdf` automatically sets the primary target to `DOCX`.
   - Dropping a `.docx` automatically sets the primary target to `PDF`.
3. **Smooth Micro-Interactions:**
   - Non-blocking asynchronous file upload via `XMLHttpRequest` with real-time `onprogress` percentage.
   - Direct browser download triggered via `Blob` URL.
   - Single-click "Reset / Convert Another" flow.

---

## 6. Edge Cases & Robustness Strategy ("Zero Glitch")

| Scenario | Risk | Mitigation Strategy |
|---|---|---|
| **Encrypted/Password PDF** | Process crashes or hangs | Detect encryption via `fitz.Document.is_encrypted` or `pypdf.PdfReader.is_encrypted` immediately during validation; return HTTP 422 with a clear explanation. |
| **Scanned/Image-Only PDF** | Empty Word document generated | Inspect text density; if character count is below threshold, output formatted images or pass through OCR pre-processing. |
| **Missing Fonts on Server** | LibreOffice substitutes fonts, distorting layout | Package standard Microsoft TrueType and Liberation fonts directly inside the Docker runtime container. |
| **Large File Uploads (> 50MB)** | High memory usage / OOM | Stream incoming file directly to disk rather than buffering in RAM. |
| **Zombie Headless Processes** | LibreOffice processes hanging indefinitely | Wrap external execution in `asyncio.wait_for(timeout=60)` and ensure process tree termination on timeout. |

---

## 7. Containerization & Deployment

### 7.1 Multi-Stage Production `Dockerfile`
```dockerfile
FROM python:3.11-slim-bookworm

# Install LibreOffice headless and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-calc \
    fonts-liberation \
    fonts-dejavu \
    fonts-freefont-ttf \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Expose port
EXPOSE 8000

# Start server with Uvicorn
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 Running Locally
```bash
# 1. Clone repository
git clone https://github.com/<your-username>/PDF-Docs-Converter.git
cd PDF-Docs-Converter

# 2. Run with Docker Compose (Recommended - includes LibreOffice & fonts)
docker-compose up --build

# Or run natively in Python (Requires LibreOffice installed locally for DOCX->PDF):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

### 7.3 Live Deployment
- **Render / Railway / Fly.io:** Deploy as a Docker service directly from GitHub. The included `Dockerfile` installs all rendering engines and runs the web app seamlessly.
- **Vercel / Netlify:** Static frontend can be deployed independently, communicating with the containerized backend API via environment variables.

---

## 8. Milestone Execution Roadmap

- [x] **Milestone 1: Documentation & Specifications** (Context, Architecture, Implementation docs created).
- [ ] **Milestone 2: Backend Core & Validators** (FastAPI app, validation pipeline, exception hierarchy).
- [ ] **Milestone 3: Core Conversion Engines** (`pdf2docx` integration + LibreOffice headless wrapper).
- [ ] **Milestone 4: Modern Minimal Web UI** (Single-page drag-and-drop, progress animations, instant download).
- [ ] **Milestone 5: Extended Features** (PDF compress, merge, and split endpoints).
- [ ] **Milestone 6: Dockerization & Testing** (Multi-stage build, automated tests, memory leak checks).
- [ ] **Milestone 7: GitHub Setup & Live Deployment** (CI pipeline, deploy configurations).
