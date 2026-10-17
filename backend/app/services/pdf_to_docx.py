"""
PDF to DOCX Conversion Service
==============================
Translates static PDF page representations into fully editable OpenXML Word documents.
Utilizes pdf2docx (powered by PyMuPDF and python-docx) to reconstruct paragraphs,
table cell grids, text formatting, and image placements with high visual fidelity.
"""

import os
import asyncio
from pathlib import Path
from pdf2docx import Converter
from backend.app.core.exceptions import ConversionError


async def convert_pdf_to_docx(input_path: Path, output_path: Path) -> Path:
    """
    Executes PDF to DOCX transformation:
    1. Spawns conversion inside Python's thread pool executor to prevent blocking
       FastAPI's asynchronous event loop during CPU-intensive layout parsing.
    2. Reconstructs text hierarchies, line flows, font weights, and table matrices.
    3. Validates that the generated output exists and is non-empty before returning.
    """
    def _execute():
        cv = None
        try:
            # Initialize pdf2docx converter engine on the source PDF
            cv = Converter(str(input_path))
            
            # Convert all pages (from start=0 to end=None)
            cv.convert(str(output_path), start=0, end=None)
        except Exception as e:
            raise ConversionError(f"PDF to DOCX layout reconstruction failed: {str(e)}")
        finally:
            if cv:
                try:
                    cv.close()
                except Exception:
                    pass

    # Offload CPU-bound task to default threadpool executor
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _execute)

    # Post-conversion sanity check
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConversionError("The DOCX output file could not be generated or is empty.")

    return output_path
