import urllib.parse
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from backend.app.core.storage import TempWorkspace, delayed_cleanup
from backend.app.core.validator import validate_pdf_file, validate_docx_file
from backend.app.services.pdf_to_docx import convert_pdf_to_docx
from backend.app.services.docx_to_pdf import convert_docx_to_pdf

router = APIRouter(prefix="/api/convert", tags=["Conversion"])

@router.post("/pdf-to-docx")
async def api_pdf_to_docx(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Converts an uploaded PDF to DOCX with high fidelity."""
    workspace = TempWorkspace()
    input_path = await workspace.save_upload(file, file.filename or "document.pdf")
    
    # Validation
    validate_pdf_file(input_path)
    
    # Conversion
    output_filename = f"{input_path.stem}.docx"
    output_path = workspace.dir / output_filename
    await convert_pdf_to_docx(input_path, output_path)

    # Schedule auto-cleanup of this ephemeral workspace
    background_tasks.add_task(delayed_cleanup, workspace, delay_seconds=180)

    # Return file download
    encoded_filename = urllib.parse.quote(output_filename)
    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=output_filename,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@router.post("/docx-to-pdf")
async def api_docx_to_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Converts an uploaded DOCX to PDF."""
    workspace = TempWorkspace()
    input_path = await workspace.save_upload(file, file.filename or "document.docx")

    # Validation
    validate_docx_file(input_path)

    # Conversion
    output_path = await convert_docx_to_pdf(input_path, workspace.dir)
    output_filename = output_path.name

    # Schedule auto-cleanup
    background_tasks.add_task(delayed_cleanup, workspace, delay_seconds=180)

    encoded_filename = urllib.parse.quote(output_filename)
    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=output_filename,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )
