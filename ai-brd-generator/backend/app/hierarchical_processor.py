import json
import re
import time
from openai import OpenAI
from backend.app.config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL

# ---------------------------------------------------------------------------
# Intermediate structure keys
# ---------------------------------------------------------------------------

BRD_KEYS = [
    "business_problem",
    "objectives",
    "stakeholders",
    "functional_requirements",
    "non_functional_requirements",
    "business_rules",
    "assumptions",
    "constraints",
    "dependencies",
    "risks",
    "success_criteria",
]

_EXTRACTION_SYSTEM_PROMPT = """You are a business analyst assistant.
Extract business requirements information from the provided text chunk.

Return ONLY a valid JSON object with exactly these keys:
{
  "business_problem": [],
  "objectives": [],
  "stakeholders": [],
  "functional_requirements": [],
  "non_functional_requirements": [],
  "business_rules": [],
  "assumptions": [],
  "constraints": [],
  "dependencies": [],
  "risks": [],
  "success_criteria": []
}

Rules:
- Each value must be a list of plain strings.
- Extract ONLY information explicitly present in the text.
- Do NOT invent or hallucinate requirements.
- If a category has no information in the text, return an empty list [].
- Do NOT wrap the JSON in markdown code fences.
- Output raw JSON only."""


def empty_intermediate() -> dict:
    """Return a blank intermediate structure."""
    return {key: [] for key in BRD_KEYS}


def extract_from_chunk(chunk: dict) -> dict:
    """
    Send one chunk to the LLM and return a structured intermediate dict.
    Each extracted item is stored as {"text": "...", "source_chunk": N}.
    On failure, returns an empty intermediate with an error note.
    """
    chunk_id = chunk.get("chunk_id", 0)
    text = chunk.get("text", "").strip()

    if not text:
        return empty_intermediate()

    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

    raw = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Text chunk:\n\n{text}"},
                ],
                temperature=0.0,
                max_tokens=4000,
                timeout=90,
            )
            raw = response.choices[0].message.content
            if raw and raw.strip():
                break
            print(f"  [WARNING] Chunk {chunk_id} attempt {attempt+1} returned empty, retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"  [WARNING] Chunk {chunk_id} attempt {attempt+1} failed: {e}")
            time.sleep(2)

    if not raw or not raw.strip():
        print(f"  [WARNING] Chunk {chunk_id} all attempts returned empty.")
        return empty_intermediate()

    try:
        parsed = _parse_json_response(raw)
    except Exception as e:
        print(f"  [WARNING] Chunk {chunk_id} JSON parse failed: {e}")
        return empty_intermediate()

    # Attach source_chunk to every extracted item
    result = empty_intermediate()
    for key in BRD_KEYS:
        items = parsed.get(key, [])
        if not isinstance(items, list):
            items = []
        for item in items:
            if isinstance(item, str) and item.strip():
                result[key].append({"text": item.strip(), "source_chunk": chunk_id})

    return result


def aggregate(chunk_results: list[dict]) -> dict:
    """
    Merge all per-chunk intermediate dicts into one combined structure.
    Performs exact-string deduplication per section.
    Assigns stable FR-NNN / NFR-NNN IDs to requirements.
    """
    combined = empty_intermediate()

    for chunk_result in chunk_results:
        for key in BRD_KEYS:
            for item in chunk_result.get(key, []):
                if not _is_duplicate(item["text"], combined[key]):
                    combined[key].append(item)

    _assign_requirement_ids(combined)
    return combined


def format_for_final_generation(aggregated: dict) -> str:
    """
    Serialize the aggregated intermediate dict into a readable text block
    that the final BRD generator can consume.
    """
    lines = []
    labels = {
        "business_problem": "Business Problem",
        "objectives": "Business Objectives",
        "stakeholders": "Stakeholders",
        "functional_requirements": "Functional Requirements",
        "non_functional_requirements": "Non-Functional Requirements",
        "business_rules": "Business Rules",
        "assumptions": "Assumptions",
        "constraints": "Constraints",
        "dependencies": "Dependencies",
        "risks": "Risks",
        "success_criteria": "Success Criteria",
    }

    for key in BRD_KEYS:
        items = aggregated.get(key, [])
        lines.append(f"### {labels[key]}")
        if items:
            for item in items:
                req_id = item.get("id", "")
                prefix = f"{req_id}: " if req_id else "- "
                lines.append(f"{prefix}{item['text']}  [source: chunk {item['source_chunk']}]")
        else:
            lines.append("Not specified in the provided requirements.")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_json_response(raw: str) -> dict:
    """Extract and parse JSON from LLM response, handling markdown fences, reasoning preamble, and truncation."""
    # Strip markdown code fences
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

    # Try last { ... } block first (reasoning models put answer after thinking), then first
    for start in [raw.rfind("{"), raw.find("{")]:
        if start == -1:
            continue
        candidate = _extract_json_block(raw, start)
        if candidate:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

    # Truncated JSON recovery — model hit token limit mid-response
    # Find the opening brace and try to salvage completed key-value pairs
    start = raw.find("{")
    if start != -1:
        partial = raw[start:]
        recovered = _recover_truncated_json(partial)
        if recovered:
            return recovered

    return {}


def _extract_json_block(text: str, start: int) -> str:
    """Extract a complete JSON object starting at position start."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return ""


def _recover_truncated_json(partial: str) -> dict:
    """Salvage key-value pairs from a truncated JSON object."""
    result = empty_intermediate()
    # Match completed list values: "key": ["item1", "item2"]
    pattern = re.compile(
        r'"(' + '|'.join(BRD_KEYS) + r')"\s*:\s*(\[[^\]]*\])',
        re.DOTALL
    )
    found_any = False
    for match in pattern.finditer(partial):
        key = match.group(1)
        try:
            value = json.loads(match.group(2))
            if isinstance(value, list):
                result[key] = value
                found_any = True
        except json.JSONDecodeError:
            pass
    return result if found_any else {}


def _is_duplicate(text: str, existing: list[dict]) -> bool:
    """Exact-string duplicate check (case-insensitive)."""
    text_lower = text.lower().strip()
    return any(item["text"].lower().strip() == text_lower for item in existing)


def _assign_requirement_ids(combined: dict) -> None:
    """Assign FR-NNN and NFR-NNN IDs in-place."""
    for i, item in enumerate(combined["functional_requirements"], start=1):
        item["id"] = f"FR-{i:03d}"
    for i, item in enumerate(combined["non_functional_requirements"], start=1):
        item["id"] = f"NFR-{i:03d}"
