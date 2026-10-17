"""
PDF Manipulation Utilities (Merge & Split)
===========================================
High-speed PDF page assembly and extraction routines powered by PyMuPDF (MuPDF C engine).
Operates directly on binary page trees for near-instant execution without re-encoding artifacts.
"""

import asyncio
import fitz  # PyMuPDF
from pathlib import Path
from backend.app.core.exceptions import ConversionError


async def merge_pdfs(input_paths: list[Path], output_path: Path) -> Path:
    """
    Merges multiple PDF documents into a single sequential PDF.
    Preserves vector graphics, annotations, and original page geometry.
    """
    def _execute():
        try:
            merged_doc = fitz.open()
            for path in input_paths:
                doc = fitz.open(path)
                merged_doc.insert_pdf(doc)
                doc.close()
            merged_doc.save(str(output_path))
            merged_doc.close()
        except Exception as e:
            raise ConversionError(f"PDF merge operation failed: {str(e)}")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _execute)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConversionError("Merged PDF was not generated or is empty.")

    return output_path


async def split_pdf(input_path: Path, output_path: Path, page_range: str) -> Path:
    """
    Extracts designated pages from a PDF document into a new PDF.
    
    Parameters:
        input_path: Path to source PDF.
        output_path: Destination path for extracted pages.
        page_range: Human-readable 1-indexed page specification (e.g., '1-3, 5, 8').
    """
    def _execute():
        try:
            doc = fitz.open(input_path)
            total_pages = len(doc)
            selected_pages = []

            # Parse user range syntax (supports commas and hyphens, e.g. "1-4, 7, 10")
            parts = [p.strip() for p in page_range.split(",") if p.strip()]
            for part in parts:
                if "-" in part:
                    start_s, end_s = part.split("-", 1)
                    start = max(1, int(start_s.strip()))
                    end = min(total_pages, int(end_s.strip()))
                    for p_num in range(start, end + 1):
                        selected_pages.append(p_num - 1)  # Convert to 0-indexed internal page numbers
                else:
                    p_num = int(part)
                    if 1 <= p_num <= total_pages:
                        selected_pages.append(p_num - 1)

            if not selected_pages:
                raise ConversionError(f"No valid pages found in range '{page_range}'. Document has {total_pages} pages.")

            # Deduplicate page list while preserving user-defined ordering
            selected_pages = list(dict.fromkeys(selected_pages))

            # Assemble target document from selected page indices
            split_doc = fitz.open()
            for p in selected_pages:
                split_doc.insert_pdf(doc, from_page=p, to_page=p)

            split_doc.save(str(output_path))
            split_doc.close()
            doc.close()
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(f"PDF extraction failed: {str(e)}")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _execute)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConversionError("Extracted PDF could not be generated.")

    return output_path
