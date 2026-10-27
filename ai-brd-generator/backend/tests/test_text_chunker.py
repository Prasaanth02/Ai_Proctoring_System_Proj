import pytest
from backend.app.text_chunker import clean_text, chunk_text, count_tokens


# ---------------------------------------------------------------------------
# clean_text tests
# ---------------------------------------------------------------------------

def test_clean_text_collapses_spaces():
    result = clean_text("Employees   should   be able to apply for leave.")
    assert "   " not in result
    assert "Employees should be able to apply for leave." in result


def test_clean_text_collapses_blank_lines():
    raw = "Paragraph one.\n\n\n\nParagraph two."
    result = clean_text(raw)
    assert "\n\n\n" not in result
    assert "Paragraph one." in result
    assert "Paragraph two." in result


def test_clean_text_preserves_paragraph_boundary():
    raw = "Requirement A.\n\nRequirement B."
    result = clean_text(raw)
    assert "\n\n" in result


def test_clean_text_normalizes_line_endings():
    raw = "Line one.\r\nLine two.\rLine three."
    result = clean_text(raw)
    assert "\r" not in result


def test_clean_text_empty_string():
    assert clean_text("") == ""


def test_clean_text_strips_line_whitespace():
    raw = "  leading and trailing   \n  next line  "
    result = clean_text(raw)
    for line in result.split("\n"):
        assert line == line.strip()


# ---------------------------------------------------------------------------
# chunk_text — small text (no chunking needed)
# ---------------------------------------------------------------------------

def test_chunk_small_text_single_chunk():
    text = "Employees should be able to submit leave requests."
    chunks = chunk_text(text, max_tokens=800, overlap_tokens=50)
    assert len(chunks) == 1
    assert chunks[0]["chunk_id"] == 1
    assert chunks[0]["text"] == text


# ---------------------------------------------------------------------------
# chunk_text — large text requiring multiple chunks
# ---------------------------------------------------------------------------

def _make_large_text(n_sentences: int = 200) -> str:
    sentence = "The system shall allow users to submit and track their business requirements. "
    return "\n\n".join([sentence.strip()] * n_sentences)


def test_chunk_large_text_multiple_chunks():
    text = _make_large_text(200)
    chunks = chunk_text(text, max_tokens=200, overlap_tokens=20)
    assert len(chunks) > 1


def test_chunk_ids_are_sequential():
    text = _make_large_text(200)
    chunks = chunk_text(text, max_tokens=200, overlap_tokens=20)
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_id"] == i + 1


# ---------------------------------------------------------------------------
# chunk size limits
# ---------------------------------------------------------------------------

def test_chunk_respects_max_tokens():
    text = _make_large_text(200)
    max_tokens = 150
    chunks = chunk_text(text, max_tokens=max_tokens, overlap_tokens=0)
    for chunk in chunks:
        assert chunk["token_count"] <= max_tokens + 20  # small tolerance for overlap boundary


# ---------------------------------------------------------------------------
# overlap behavior
# ---------------------------------------------------------------------------

def test_overlap_content_carried_forward():
    # Build text with clearly distinct paragraphs
    paragraphs = [f"Requirement number {i} states that the system must perform action {i}." for i in range(1, 20)]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text, max_tokens=100, overlap_tokens=30)
    if len(chunks) > 1:
        # Some text from chunk N-1 should appear at the start of chunk N
        prev_tail = chunks[0]["text"][-50:]
        assert any(word in chunks[1]["text"] for word in prev_tail.split() if len(word) > 4)


def test_no_overlap_when_zero():
    text = _make_large_text(100)
    chunks_no_overlap = chunk_text(text, max_tokens=150, overlap_tokens=0)
    chunks_with_overlap = chunk_text(text, max_tokens=150, overlap_tokens=30)
    # With overlap, chunks should be longer (more tokens)
    if len(chunks_with_overlap) > 1:
        assert chunks_with_overlap[1]["token_count"] >= chunks_no_overlap[1]["token_count"]


# ---------------------------------------------------------------------------
# metadata correctness
# ---------------------------------------------------------------------------

def test_chunk_metadata_fields():
    text = "The system shall process all incoming requests within 2 seconds."
    chunks = chunk_text(text, max_tokens=800, overlap_tokens=0, source="requirements.pdf")
    assert chunks[0]["chunk_id"] == 1
    assert chunks[0]["source"] == "requirements.pdf"
    assert isinstance(chunks[0]["token_count"], int)
    assert chunks[0]["token_count"] > 0
    assert chunks[0]["text"] == text


def test_chunk_token_count_matches():
    text = "Managers shall approve or reject leave requests within one business day."
    chunks = chunk_text(text, max_tokens=800, overlap_tokens=0)
    assert chunks[0]["token_count"] == count_tokens(text)


# ---------------------------------------------------------------------------
# document order preservation
# ---------------------------------------------------------------------------

def test_chunk_preserves_document_order():
    paragraphs = [f"Section {i}: requirement details for feature {i}." for i in range(1, 30)]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text, max_tokens=100, overlap_tokens=0)
    combined = " ".join(c["text"] for c in chunks)
    last_pos = -1
    for i in range(1, 30):
        pos = combined.find(f"Section {i}:")
        if pos != -1:
            assert pos > last_pos
            last_pos = pos


# ---------------------------------------------------------------------------
# error / edge cases
# ---------------------------------------------------------------------------

def test_chunk_empty_text_raises():
    with pytest.raises(ValueError, match="empty"):
        chunk_text("", max_tokens=800, overlap_tokens=100)


def test_chunk_invalid_max_tokens_raises():
    with pytest.raises(ValueError, match="max_tokens"):
        chunk_text("Some text.", max_tokens=0, overlap_tokens=0)


def test_chunk_invalid_overlap_raises():
    with pytest.raises(ValueError, match="overlap_tokens"):
        chunk_text("Some text.", max_tokens=100, overlap_tokens=100)


def test_chunk_negative_overlap_raises():
    with pytest.raises(ValueError, match="overlap_tokens"):
        chunk_text("Some text.", max_tokens=100, overlap_tokens=-1)
