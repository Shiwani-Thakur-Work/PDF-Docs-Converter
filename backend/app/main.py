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

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

async def periodic_cleanup_task():
    """Runs a background loop every 5 minutes to sweep abandoned temp directories."""
    while True:
        try:
            cleanup_stale_workspaces()
        except Exception:
            pass
        await asyncio.sleep(300)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run immediate cleanup and start background sweeper
    cleanup_stale_workspaces()
    cleanup_task = asyncio.create_task(periodic_cleanup_task())
    yield
    # Shutdown
    cleanup_task.cancel()

app = FastAPI(
    title="PDF & Docs Converter API",
    description="High-fidelity, zero-glitch bi-directional document converter suite.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for universal access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handlers
@app.exception_handler(AppBaseException)
async def handle_app_exception(request: Request, exc: AppBaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.message}
    )

@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": f"An unexpected error occurred: {str(exc)}"}
    )

# Register API Endpoints
app.include_router(convert_router)
app.include_router(tools_router)
app.include_router(health_router)

# Mount Static Frontend Files
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")
