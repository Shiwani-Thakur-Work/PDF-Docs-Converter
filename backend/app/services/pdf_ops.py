import asyncio
import fitz  # PyMuPDF
from pathlib import Path
from backend.app.core.exceptions import ConversionError

async def merge_pdfs(input_paths: list[Path], output_path: Path) -> Path:
    """Merges multiple PDF documents into a single unified PDF."""
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
            raise ConversionError(f"PDF merge failed: {str(e)}")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _execute)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConversionError("Merged PDF was not generated or is empty.")

    return output_path

async def split_pdf(input_path: Path, output_path: Path, page_range: str) -> Path:
    """
    Extracts specified pages from a PDF.
    Supports formats like '1-3', '1,3,5', or '2'.
    Page numbering is 1-indexed for the user.
    """
    def _execute():
        try:
            doc = fitz.open(input_path)
            total_pages = len(doc)
            selected_pages = []

            # Parse page_range string
            parts = [p.strip() for p in page_range.split(",") if p.strip()]
            for part in parts:
                if "-" in part:
                    start_s, end_s = part.split("-", 1)
                    start = max(1, int(start_s.strip()))
                    end = min(total_pages, int(end_s.strip()))
                    for p_num in range(start, end + 1):
                        selected_pages.append(p_num - 1)
                else:
                    p_num = int(part)
                    if 1 <= p_num <= total_pages:
                        selected_pages.append(p_num - 1)

            if not selected_pages:
                raise ConversionError(f"No valid pages found in range '{page_range}'. Document has {total_pages} pages.")

            # Deduplicate while preserving order
            selected_pages = list(dict.fromkeys(selected_pages))

            split_doc = fitz.open()
            for p in selected_pages:
                split_doc.insert_pdf(doc, from_page=p, to_page=p)

            split_doc.save(str(output_path))
            split_doc.close()
            doc.close()
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(f"PDF split failed: {str(e)}")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _execute)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConversionError("Split PDF was not generated.")

    return output_path
