import fitz
from fastapi import APIRouter
from backend.app.services.docx_to_pdf import find_libreoffice
from backend.app.config import MAX_FILE_SIZE_MB, FILE_TTL_SECONDS

router = APIRouter(prefix="/api/health", tags=["Health & Status"])

@router.get("")
async def get_health_status():
    """Returns engine availability and runtime diagnostic status."""
    libreoffice_bin = find_libreoffice()
    return {
        "status": "healthy",
        "engines": {
            "pdf2docx": "ready",
            "pymupdf_version": fitz.__version__,
            "docx2pdf_libreoffice": "available" if libreoffice_bin else "fallback_reportlab_active",
            "libreoffice_path": libreoffice_bin
        },
        "limits": {
            "max_file_size_mb": MAX_FILE_SIZE_MB,
            "ephemeral_ttl_seconds": FILE_TTL_SECONDS
        }
    }
