import urllib.parse
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from backend.app.core.storage import TempWorkspace, delayed_cleanup
from backend.app.core.validator import validate_pdf_file
from backend.app.services.pdf_compress import compress_pdf
from backend.app.services.pdf_ops import merge_pdfs, split_pdf

router = APIRouter(prefix="/api/tools", tags=["PDF Utilities"])

@router.post("/compress-pdf")
async def api_compress_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    level: str = Form("medium")
):
    """Compresses a PDF file."""
    workspace = TempWorkspace()
    input_path = await workspace.save_upload(file, file.filename or "document.pdf")
    validate_pdf_file(input_path)

    output_filename = f"{input_path.stem}_compressed.pdf"
    output_path = workspace.dir / output_filename
    await compress_pdf(input_path, output_path, level=level)

    background_tasks.add_task(delayed_cleanup, workspace, delay_seconds=180)

    encoded_filename = urllib.parse.quote(output_filename)
    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=output_filename,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@router.post("/merge-pdf")
async def api_merge_pdf(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...)
):
    """Merges multiple PDF files into one."""
    if len(files) < 2:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Please provide at least two PDF files to merge.")

    workspace = TempWorkspace()
    saved_paths = []
    for f in files:
        path = await workspace.save_upload(f, f.filename or "doc.pdf")
        validate_pdf_file(path)
        saved_paths.append(path)

    output_filename = "merged_document.pdf"
    output_path = workspace.dir / output_filename
    await merge_pdfs(saved_paths, output_path)

    background_tasks.add_task(delayed_cleanup, workspace, delay_seconds=180)

    encoded_filename = urllib.parse.quote(output_filename)
    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=output_filename,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@router.post("/split-pdf")
async def api_split_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pages: str = Form(...)
):
    """Extracts specified pages from a PDF."""
    workspace = TempWorkspace()
    input_path = await workspace.save_upload(file, file.filename or "document.pdf")
    validate_pdf_file(input_path)

    output_filename = f"{input_path.stem}_split.pdf"
    output_path = workspace.dir / output_filename
    await split_pdf(input_path, output_path, page_range=pages)

    background_tasks.add_task(delayed_cleanup, workspace, delay_seconds=180)

    encoded_filename = urllib.parse.quote(output_filename)
    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=output_filename,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )
