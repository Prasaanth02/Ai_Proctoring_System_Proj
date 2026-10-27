import os
import pytest
import fitz
from backend.app.document_processor import extract_text


def test_extract_txt(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("This is a business requirement document.", encoding="utf-8")
    result = extract_text(str(f))
    assert "business requirement" in result


def test_extract_pdf(tmp_path):
    pdf_path = str(tmp_path / "sample.pdf")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Business requirement from PDF.")
    doc.save(pdf_path)
    doc.close()

    result = extract_text(pdf_path)
    assert "Business requirement" in result


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        extract_text("nonexistent_file.txt")


def test_unsupported_file_type(tmp_path):
    f = tmp_path / "file.docx"
    f.write_bytes(b"fake docx content")
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text(str(f))


def test_empty_txt_file(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("   ", encoding="utf-8")
    with pytest.raises(ValueError, match="No meaningful text"):
        extract_text(str(f))


def test_empty_pdf(tmp_path):
    pdf_path = str(tmp_path / "empty.pdf")
    doc = fitz.open()
    doc.new_page()  # blank page, no text
    doc.save(pdf_path)
    doc.close()
    with pytest.raises(ValueError, match="No meaningful text"):
        extract_text(pdf_path)
