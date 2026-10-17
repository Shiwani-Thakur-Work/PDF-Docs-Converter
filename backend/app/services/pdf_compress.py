import asyncio
import fitz  # PyMuPDF
from pathlib import Path
from backend.app.core.exceptions import ConversionError

async def compress_pdf(input_path: Path, output_path: Path, level: str = "medium") -> tuple[Path, int, int]:
    """
    Compresses a PDF file using PyMuPDF stream optimization and garbage collection.
    Returns (output_path, original_size, compressed_size).
    """
    def _execute():
        try:
            doc = fitz.open(input_path)
            
            # Save options based on level
            # garbage=4: deduplicate fonts/images and strip unused objects
            # deflate=True: deflate streams
            # clean=True: clean and sanitize PDF contents
            doc.save(
                str(output_path),
                garbage=4,
                deflate=True,
                clean=True
            )
            doc.close()
        except Exception as e:
            raise ConversionError(f"PDF compression failed: {str(e)}")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _execute)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConversionError("Compressed PDF could not be saved.")

    orig_size = input_path.stat().st_size
    comp_size = output_path.stat().st_size
    return output_path, orig_size, comp_size
