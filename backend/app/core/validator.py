"""
File Ingestion & Defensive Validation
=====================================
Performs strict pre-conversion checks on all uploaded files. Prevents pipeline
crashes, malformed inputs, malicious payload masquerading, and unhandled password
locks before invoking heavy rendering engines.
"""

import os
import zipfile
import fitz  # PyMuPDF
from pathlib import Path
from backend.app.config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from backend.app.core.exceptions import ValidationError, PasswordProtectedError


def validate_file_size(file_path: Path):
    """
    Verifies that the uploaded file contains data and does not exceed the allowed threshold.
    Rejects 0-byte placeholders and files exceeding MAX_FILE_SIZE_MB.
    """
    size = os.path.getsize(file_path)
    if size == 0:
        raise ValidationError("The uploaded file is empty (0 bytes).")
    if size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File size exceeds the maximum limit of {MAX_FILE_SIZE_MB}MB.")


def validate_pdf_file(file_path: Path):
    """
    Validates PDF format integrity, binary signature, and encryption state:
    1. Size boundary checks.
    2. Magic bytes header inspection (must begin with '%PDF-').
    3. Encryption check: Detects password-protected PDFs and returns a helpful message
       instead of failing inside conversion routines.
    4. Structural health check: Ensures document has at least one readable page.
    """
    validate_file_size(file_path)

    # 1. Inspect Magic Number (First 5 bytes of the binary stream)
    # Rejects files renamed with a .pdf extension that are not actual PDFs
    with open(file_path, "rb") as f:
        header = f.read(5)
        if header != b"%PDF-":
            raise ValidationError("Invalid PDF format. The file does not have a valid PDF binary header.")

    # 2. Structural & Encryption Analysis
    try:
        doc = fitz.open(file_path)
        if doc.is_encrypted:
            doc.close()
            raise PasswordProtectedError()

        page_count = len(doc)
        doc.close()

        if page_count == 0:
            raise ValidationError("The PDF document contains no pages or has an empty page tree.")
    except PasswordProtectedError:
        raise
    except Exception as e:
        raise ValidationError(f"Corrupt or unreadable PDF document: {str(e)}")


def validate_docx_file(file_path: Path):
    """
    Validates Microsoft Word (.docx) package structure:
    1. Size boundary checks.
    2. Magic bytes header inspection: Verifies PK zip archive signature (0x50 0x4B 0x03 0x04).
    3. OpenXML schema validation: Confirms internal presence of '[Content_Types].xml',
       distinguishing real Word archives from arbitrary zip archives.
    """
    validate_file_size(file_path)

    # 1. Magic bytes check for PK zip header
    with open(file_path, "rb") as f:
        header = f.read(4)
        if header != b"PK\x03\x04":
            raise ValidationError("Invalid DOCX format. Expected a valid OpenXML document archive.")

    # 2. OpenXML Container Validation
    try:
        with zipfile.ZipFile(file_path, "r") as z:
            namelist = z.namelist()
            if "[Content_Types].xml" not in namelist:
                raise ValidationError("The file is not a valid DOCX document (missing [Content_Types].xml).")
    except zipfile.BadZipFile:
        raise ValidationError("The DOCX file archive is corrupt or incomplete.")
    except Exception as e:
        raise ValidationError(f"Error inspecting DOCX document: {str(e)}")
