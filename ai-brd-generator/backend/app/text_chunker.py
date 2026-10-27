import re
import os
from dotenv import load_dotenv
load_dotenv()
import tiktoken

# Encoding used by GPT-4o and most modern OpenAI-compatible models
_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_ENCODING.encode(text))


def clean_text(text: str) -> str:
    """
    Normalize raw extracted text:
    - Collapse runs of spaces/tabs into a single space per line
    - Collapse 3+ consecutive blank lines into exactly one blank line
    - Strip leading/trailing whitespace from each line
    - Preserve paragraph boundaries (single blank line between paragraphs)
    """
    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip trailing whitespace from every line, collapse internal spaces/tabs
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

    # Collapse 3+ consecutive blank lines into one blank line
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def chunk_text(
    text: str,
    max_tokens: int = 800,
    overlap_tokens: int = 100,
    source: str = "",
) -> list[dict]:
    """
    Split cleaned text into token-aware chunks with overlap.

    Strategy (in priority order):
      1. Paragraph boundaries  (\n\n)
      2. Sentence boundaries   (. / ? / !)
      3. Hard token cut        (last resort)

    Returns a list of chunk dicts:
      { chunk_id, text, source, token_count }
    """
    if not text or not text.strip():
        raise ValueError("Text is empty. Cannot chunk.")
    if max_tokens < 1:
        raise ValueError("max_tokens must be at least 1.")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens cannot be negative.")
    if overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be less than max_tokens.")

    paragraphs = _split_into_paragraphs(text)
    raw_chunks = _build_chunks(paragraphs, max_tokens)
    chunks_with_overlap = _apply_overlap(raw_chunks, overlap_tokens)

    source_name = os.path.basename(source) if source else ""

    return [
        {
            "chunk_id": idx + 1,
            "text": chunk,
            "source": source_name,
            "token_count": count_tokens(chunk),
        }
        for idx, chunk in enumerate(chunks_with_overlap)
    ]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _split_into_paragraphs(text: str) -> list[str]:
    """Split on blank lines; further split oversized paragraphs into sentences."""
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    result = []
    for para in paragraphs:
        result.extend(_split_paragraph_into_sentences(para))
    return result


def _split_paragraph_into_sentences(paragraph: str) -> list[str]:
    """
    Return the paragraph as-is if it is a single sentence or short.
    Otherwise split on sentence-ending punctuation.
    """
    # Simple sentence splitter: split after . ? ! followed by whitespace
    sentences = re.split(r"(?<=[.?!])\s+", paragraph)
    return [s.strip() for s in sentences if s.strip()]


def _build_chunks(units: list[str], max_tokens: int) -> list[str]:
    """
    Greedily pack units (sentences/paragraphs) into chunks
    without exceeding max_tokens.
    """
    chunks = []
    current_parts: list[str] = []
    current_tokens = 0

    for unit in units:
        unit_tokens = count_tokens(unit)

        # Unit alone exceeds max_tokens — hard-split it
        if unit_tokens > max_tokens:
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = []
                current_tokens = 0
            chunks.extend(_hard_split(unit, max_tokens))
            continue

        if current_tokens + unit_tokens > max_tokens:
            chunks.append("\n\n".join(current_parts))
            current_parts = [unit]
            current_tokens = unit_tokens
        else:
            current_parts.append(unit)
            current_tokens += unit_tokens

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks


def _hard_split(text: str, max_tokens: int) -> list[str]:
    """Split a single oversized unit by token boundary as a last resort."""
    tokens = _ENCODING.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i: i + max_tokens]
        chunks.append(_ENCODING.decode(chunk_tokens))
    return chunks


def _apply_overlap(chunks: list[str], overlap_tokens: int) -> list[str]:
    """
    Prepend the tail of the previous chunk (up to overlap_tokens)
    to each subsequent chunk.
    """
    if overlap_tokens == 0 or len(chunks) <= 1:
        return chunks

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tokens = _ENCODING.encode(chunks[i - 1])
        overlap_text = _ENCODING.decode(prev_tokens[-overlap_tokens:])
        result.append(overlap_text + "\n\n" + chunks[i])

    return result
