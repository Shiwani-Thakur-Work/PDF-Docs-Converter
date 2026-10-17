import os
import zipfile
import fitz  # PyMuPDF
from pathlib import Path
from backend.app.config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from backend.app.core.exceptions import ValidationError, PasswordProtectedError

def validate_file_size(file_path: Path):
    """Ensures file size does not exceed the allowed threshold."""
    size = os.path.getsize(file_path)
    if size == 0:
        raise ValidationError("The uploaded file is empty (0 bytes).")
    if size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File size exceeds the maximum limit of {MAX_FILE_SIZE_MB}MB.")

def validate_pdf_file(file_path: Path):
    """Validates that a file is a valid, unencrypted PDF."""
    validate_file_size(file_path)
    
    # Check magic bytes for PDF
    with open(file_path, "rb") as f:
        header = f.read(5)
        if header != b"%PDF-":
            raise ValidationError("Invalid PDF format. The file does not have a valid PDF header.")
            
    # Check for password encryption and structural validity using PyMuPDF
    try:
        doc = fitz.open(file_path)
        if doc.is_encrypted:
            doc.close()
            raise PasswordProtectedError()
        page_count = len(doc)
        doc.close()
        if page_count == 0:
            raise ValidationError("The PDF document contains no pages.")
    except PasswordProtectedError:
        raise
    except Exception as e:
        raise ValidationError(f"Corrupt or unreadable PDF: {str(e)}")

def validate_docx_file(file_path: Path):
    """Validates that a file is a valid Microsoft Word (.docx) archive."""
    validate_file_size(file_path)
    
    # Check magic bytes for PK zip header
    with open(file_path, "rb") as f:
        header = f.read(4)
        if header != b"PK\x03\x04":
            raise ValidationError("Invalid DOCX format. Expected a valid OpenXML document archive.")
            
    # Check zip integrity and presence of [Content_Types].xml
    try:
        with zipfile.ZipFile(file_path, "r") as z:
            namelist = z.namelist()
            if "[Content_Types].xml" not in namelist:
                raise ValidationError("The file is not a valid DOCX document (missing [Content_Types].xml).")
    except zipfile.BadZipFile:
        raise ValidationError("The DOCX file is corrupt or incomplete.")
    except Exception as e:
        raise ValidationError(f"Error inspecting DOCX: {str(e)}")
