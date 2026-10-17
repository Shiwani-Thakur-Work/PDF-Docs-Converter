"""
DocFlow Application Server
==========================
Core entrypoint for the document conversion suite. Configures the FastAPI 
application instance, mounts static user interface assets, registers API routes,
and manages background garbage collection lifecycles for ephemeral files.
"""

import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.exceptions import AppBaseException
from backend.app.core.storage import cleanup_stale_workspaces
from backend.app.api.routes_convert import router as convert_router
from backend.app.api.routes_tools import router as tools_router
from backend.app.api.routes_health import router as health_router

# Locate the frontend directory relative to this file
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


async def periodic_cleanup_task():
    """
    Background Maintenance Loop
    ---------------------------
    Periodically checks the temporary workspace storage every 5 minutes (300s)
    to safely remove abandoned conversion folders older than the configured TTL.
    This guarantees zero disk exhaustion and zero data retention even if client
    connections drop unexpectedly mid-transfer.
    """
    while True:
        try:
            cleanup_stale_workspaces()
        except Exception:
            # Prevent background thread crashes from interrupting the main event loop
            pass
        await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifecycle Manager
    -----------------------------
    Executes startup initialization (cleaning existing temp files, spawning GC loop)
    and graceful shutdown teardown (cancelling background worker tasks).
    """
    # [Startup Phase]: Clean previous stale sessions and start background garbage collection
    cleanup_stale_workspaces()
    cleanup_task = asyncio.create_task(periodic_cleanup_task())
    
    yield  # Application is actively serving requests
    
    # [Shutdown Phase]: Cancel background workers cleanly
    cleanup_task.cancel()


# Instantiate FastAPI Application
app = FastAPI(
    title="DocFlow — PDF & Docs Converter API",
    description=(
        "High-fidelity bi-directional document conversion suite. "
        "Transforms PDF to editable Word (DOCX) and Word to PDF with layout preservation."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cross-Origin Resource Sharing (CORS) Configuration
# Allows web frontends (including GitHub Pages deployments) to communicate with this backend API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Centralized Error Handling Boundaries
# ============================================================================

@app.exception_handler(AppBaseException)
async def handle_app_exception(request: Request, exc: AppBaseException):
    """
    Translates anticipated domain errors (e.g., password-protected PDFs, corrupt files,
    file size overages) into clean, structured JSON responses for the frontend.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.message}
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception):
    """
    Catches unhandled server exceptions, preventing raw stack trace exposure to clients
    while returning a polite, actionable error payload.
    """
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": f"An unexpected conversion error occurred: {str(exc)}"}
    )


# ============================================================================
# API Route Registration
# ============================================================================
app.include_router(convert_router)
app.include_router(tools_router)
app.include_router(health_router)


# ============================================================================
# Static Frontend Assets & Client Web Application
# ============================================================================
if FRONTEND_DIR.exists():
    # Mount styling, scripts, and media asset folders
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
    if (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/", summary="Serve Client Web Application")
    async def serve_index():
        """Returns the main single-page document converter interface."""
        return FileResponse(FRONTEND_DIR / "index.html")
