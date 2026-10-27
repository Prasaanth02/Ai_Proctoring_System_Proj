import os
import fitz  # PyMuPDF


SUPPORTED_EXTENSIONS = {".pdf", ".txt"}


def extract_text(file_path: str) -> str:
    """Extract text from a PDF or TXT file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Supported: {SUPPORTED_EXTENSIONS}")

    if ext == ".txt":
        text = _extract_from_txt(file_path)
    else:
        text = _extract_from_pdf(file_path)

    if not text or not text.strip():
        raise ValueError("No meaningful text could be extracted from the document.")

    return text.strip()


def _extract_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_from_pdf(file_path: str) -> str:
    try:
        doc = fitz.open(file_path)
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n".join(pages)
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}")
