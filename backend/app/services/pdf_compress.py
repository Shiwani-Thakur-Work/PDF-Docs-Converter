"""
PDF Compression & Optimization Service
======================================
Shrinks PDF file size using PyMuPDF's C-accelerated stream deflating, object
deduplication, and dead metadata stripping.
"""

import asyncio
import fitz  # PyMuPDF
from pathlib import Path
from backend.app.core.exceptions import ConversionError


async def compress_pdf(input_path: Path, output_path: Path, level: str = "medium") -> tuple[Path, int, int]:
    """
    Optimizes and compresses a PDF document:
    - `garbage=4`: Scans the PDF object tree, deduplicates redundant font subsets,
      and purges orphaned objects and unreferenced streams.
    - `deflate=True`: Re-compresses uncompressed streams with zlib Deflate.
    - `clean=True`: Sanitizes internal cross-reference (XREF) tables.

    Returns:
        tuple[Path, int, int]: (output_path, original_size_bytes, compressed_size_bytes)
    """
    def _execute():
        try:
            doc = fitz.open(input_path)
            doc.save(
                str(output_path),
                garbage=4,
                deflate=True,
                clean=True
            )
            doc.close()
        except Exception as e:
            raise ConversionError(f"PDF compression pipeline failed: {str(e)}")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _execute)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConversionError("Compressed PDF could not be generated.")

    orig_size = input_path.stat().st_size
    comp_size = output_path.stat().st_size
    return output_path, orig_size, comp_size
