# DocFlow — PDF & Docs Converter Suite 📄⚡

> A high-fidelity, zero-glitch, privacy-first Document Converter tool. Convert **PDF to DOCX** and **DOCX to PDF** with layout preservation, accompanied by companion PDF utilities (Compress, Merge, Split).

---

## 🌟 Key Features

- **Bi-Directional High Fidelity:**
  - `PDF ➔ DOCX`: Intelligently reconstructs tables, font styling, multi-column layouts, and images into editable Word `.docx` documents (`pdf2docx` + PyMuPDF).
  - `DOCX ➔ PDF`: Generates clean, printable, searchable PDFs with 1:1 page layout parity (Headless LibreOffice in Docker, with ReportLab pure-Python fallback for universal standalone operation).
- **Zero-Glitch & Bulletproof:**
  - Magic-byte validation (`%PDF-` and `PK\x03\x04`).
  - Pre-emptive password-protected document detection with user-friendly alerts.
  - Safe memory streaming with bounded file size thresholds.
- **Privacy & Zero Retention:**
  - Files are processed in ephemeral sandboxes and purged immediately upon download (plus automated periodic background garbage collection).
- **Minimal, Modern UI:**
  - Sleek dark-mode aesthetic with ambient glow, drag-and-drop zone, real-time conversion progress bar, and instant one-click downloads.
- **Companion Utilities:**
  - **Compress PDF:** Re-sample streams and deduplicate objects to shrink file size.
  - **Merge PDFs:** Combine multiple PDF documents into a single unified file.
  - **Split PDF:** Extract specific pages or page ranges (e.g., `1-3, 5, 8`).

---

## 📖 Architectural Documentation

Full project blueprints are stored in the [`docs/`](./docs/) directory:
- 📑 **[Context & Vision](./docs/context.md):** Problem statement, design principles, quality mandates, and feature scope.
- 🏗️ **[System Architecture](./docs/architecture.md):** Sequence diagrams, conversion pipelines, ephemeral storage, and security layers.
- 🚀 **[Implementation Guide](./docs/implementation.md):** Service designs, API contracts, edge case handling, and Docker setup.

---

## 🚀 How to Run Locally

### Option 1: One-Click Quick Start (Windows)
Simply run either script in the project root:
```powershell
# Using PowerShell:
.\run.ps1

# Or double-click / run in Command Prompt:
run.bat
```
This automatically verifies your virtual environment, launches the server, and opens `http://localhost:8000` in your default browser.

---

### Option 2: Standard Terminal Run

1. **Activate the virtual environment:**
   ```powershell
   # Windows PowerShell
   .\.venv\Scripts\activate

   # macOS / Linux
   source .venv/bin/activate
   ```

2. **Install dependencies (if not already installed):**
   ```bash
   pip install -r requirements.txt
   # OR with uv:
   uv pip install -r requirements.txt
   ```

3. **Start the server:**
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```

4. **Open your browser:**
   - Web Application UI: `http://localhost:8000`
   - Interactive Swagger API Docs: `http://localhost:8000/docs`

---

### Option 3: Run with Docker (Recommended for Production & Cloud)

Docker packages Python, LibreOffice headless, and true-type font packs in an isolated Linux container:

```bash
docker compose up --build
```
Access the application at `http://localhost:8000`.

---

## 🧪 Running Automated Tests

A comprehensive test suite is included in `tests/test_converter.py`:

```bash
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

All 5 core test cases (PDF to DOCX, DOCX to PDF, Compression, Merge/Split, and Zero-byte validation) run in ~3.8 seconds.

---

## 🌐 How to Push to GitHub & Deploy Live

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "feat: complete DocFlow PDF-Docs converter suite"
git branch -M main
git remote add origin https://github.com/<your-username>/PDF-Docs-Converter.git
git push -u origin main
```

### 2. Live Deployment (e.g. Render / Railway / Fly.io)

Because the project includes a production-ready `Dockerfile`:

1. **Render.com:**
   - Create a new **Web Service** on [Render](https://render.com).
   - Connect your GitHub repository.
   - Choose **Docker** as the Runtime environment.
   - Set Port to `8000`.
   - Deploy! Render will build the container with LibreOffice and fonts automatically.

2. **Railway.app:**
   - Click **New Project** ➔ **Deploy from GitHub repo**.
   - Railway will auto-detect the `Dockerfile` and deploy with zero extra configuration.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/convert/pdf-to-docx` | Converts PDF to editable DOCX |
| `POST` | `/api/convert/docx-to-pdf` | Converts DOCX to PDF |
| `POST` | `/api/tools/compress-pdf` | Compresses PDF streams |
| `POST` | `/api/tools/merge-pdf` | Merges multiple PDFs |
| `POST` | `/api/tools/split-pdf` | Splits PDF by page numbers/ranges |
| `GET` | `/api/health` | Health check and engine availability |

---

## 🔒 Security & Privacy Notice
All uploads are saved to isolated, UUID-tagged ephemeral directories. Files are purged immediately after the download stream finishes and cleaned up via an automated 10-minute TTL garbage collection worker. No user documents are ever persisted or retained.

---

## 📜 License
MIT License.
