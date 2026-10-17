import os
import asyncio
from pathlib import Path
from pdf2docx import Converter
from backend.app.core.exceptions import ConversionError

async def convert_pdf_to_docx(input_path: Path, output_path: Path) -> Path:
    """
    Converts a PDF file into a Microsoft Word (.docx) file with high fidelity.
    Uses pdf2docx in a background thread to prevent blocking the event loop.
    """
    def _execute():
        cv = None
        try:
            cv = Converter(str(input_path))
            cv.convert(str(output_path), start=0, end=None)
        except Exception as e:
            raise ConversionError(f"PDF to DOCX conversion failed: {str(e)}")
        finally:
            if cv:
                try:
                    cv.close()
                except Exception:
                    pass

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _execute)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConversionError("The DOCX file could not be generated or is empty.")

    return output_path
