import os
import shutil
import asyncio
import subprocess
from pathlib import Path
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from backend.app.core.exceptions import ConversionError

def find_libreoffice() -> str | None:
    """Detects LibreOffice binary across Windows, Linux, and macOS."""
    # Check PATH first
    which_soffice = shutil.which("soffice")
    if which_soffice:
        return which_soffice

    # Common Windows installation locations
    windows_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    ]
    for p in windows_paths:
        if os.path.exists(p):
            return p

    # Common macOS / Linux paths
    unix_paths = [
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    ]
    for p in unix_paths:
        if os.path.exists(p):
            return p

    return None

def _convert_docx_to_pdf_reportlab(input_path: Path, output_path: Path):
    """
    Pure-Python fallback converter using python-docx and ReportLab.
    Ensures DOCX to PDF works universally without external binaries.
    """
    try:
        doc = Document(str(input_path))
        pdf = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )
        
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontSize = 11
        normal_style.leading = 14
        
        h1_style = styles['Heading1']
        h1_style.fontSize = 18
        h1_style.leading = 22
        h1_style.spaceAfter = 8
        
        h2_style = styles['Heading2']
        h2_style.fontSize = 14
        h2_style.leading = 18
        h2_style.spaceAfter = 6

        elements = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                elements.append(Spacer(1, 8))
                continue
            
            # Select style based on paragraph style name
            style_name = p.style.name.lower() if p.style else ""
            if "heading 1" in style_name:
                curr_style = h1_style
            elif "heading 2" in style_name or "heading 3" in style_name:
                curr_style = h2_style
            else:
                curr_style = normal_style

            # Escape XML entities for ReportLab Paragraph
            safe_text = (text.replace("&", "&amp;")
                             .replace("<", "&lt;")
                             .replace(">", "&gt;"))
            elements.append(Paragraph(safe_text, curr_style))
            elements.append(Spacer(1, 6))

        for table in doc.tables:
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    cell_text = cell.text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    row_data.append(Paragraph(cell_text, normal_style))
                table_data.append(row_data)

            if table_data:
                rl_table = Table(table_data)
                rl_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                elements.append(Spacer(1, 8))
                elements.append(rl_table)
                elements.append(Spacer(1, 12))

        if not elements:
            elements.append(Paragraph("(Empty Document)", normal_style))

        pdf.build(elements)
    except Exception as e:
        raise ConversionError(f"Pure-Python DOCX to PDF conversion failed: {str(e)}")

async def convert_docx_to_pdf(input_path: Path, output_dir: Path) -> Path:
    """
    Converts DOCX to PDF. Prefers Headless LibreOffice for 1:1 fidelity,
    and falls back to the embedded ReportLab engine if LibreOffice is unavailable.
    """
    soffice_path = find_libreoffice()
    base_name = input_path.stem
    target_pdf = output_dir / f"{base_name}.pdf"

    if soffice_path:
        cmd = [
            soffice_path,
            "--headless",
            "--convert-to", "pdf:writer_pdf_Export",
            "--outdir", str(output_dir),
            str(input_path)
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60.0)
            if proc.returncode == 0 and target_pdf.exists():
                return target_pdf
        except Exception:
            # Fall back to ReportLab if LibreOffice invocation encounters an error
            pass

    # Pure Python Fallback
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _convert_docx_to_pdf_reportlab, input_path, target_pdf)

    if not target_pdf.exists() or target_pdf.stat().st_size == 0:
        raise ConversionError("Output PDF was not generated or is empty.")

    return target_pdf
