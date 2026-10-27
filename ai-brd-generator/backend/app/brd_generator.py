from openai import OpenAI
import time
from backend.app.config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL

# ---------------------------------------------------------------------------
# Phase 1 — single-shot BRD from raw source text
# ---------------------------------------------------------------------------

_BRD_SYSTEM_PROMPT = """You are a senior business analyst. Generate a Business Requirements Document (BRD) from the source text below.

STRICT RULES:
- Output ONLY the markdown BRD. No thinking. No reasoning. No notes. No preamble.
- Your very first character must be: #
- Extract information ONLY from the source text.
- Do NOT invent or hallucinate requirements.
- If a section has no information in the source, write: Not specified in the provided requirements.
- Use professional language.

Use this exact structure:

# Business Requirements Document

## 1. Project Title

## 2. Executive Summary

## 3. Business Background / Problem Statement

## 4. Business Objectives

## 5. Scope

### In Scope

### Out of Scope

## 6. Stakeholders

## 7. Functional Requirements

(Label each as FR-01, FR-02, etc.)

## 8. Non-Functional Requirements

(Label each as NFR-01, NFR-02, etc.)

## 9. Business Rules

## 10. Assumptions

## 11. Constraints

## 12. Dependencies

## 13. Risks

## 14. Success Criteria
"""

# ---------------------------------------------------------------------------
# Phase 3 — final BRD synthesis from aggregated intermediate information
# ---------------------------------------------------------------------------

_FINAL_BRD_SYSTEM_PROMPT = """You are a senior business analyst. Your task is to write a complete, \
professional Business Requirements Document (BRD) using the structured information provided below.

STRICT RULES:
- Output ONLY the markdown BRD. No thinking. No reasoning. No preamble.
- Your very first character must be: #
- Use ONLY the information provided. Do NOT invent or hallucinate requirements.
- If a section has no information provided, write: Not specified in the provided requirements.
- Use professional business language.
- Remove the [source: chunk N] annotations from the final output.
- Preserve all requirement IDs (FR-001, NFR-001, etc.) exactly as given.

Use this exact structure:

# Business Requirements Document

## 1. Project Title

## 2. Executive Summary

## 3. Business Background / Problem Statement

## 4. Business Objectives

## 5. Scope

### In Scope

### Out of Scope

## 6. Stakeholders

## 7. Functional Requirements

## 8. Non-Functional Requirements

## 9. Business Rules

## 10. Assumptions

## 11. Constraints

## 12. Dependencies

## 13. Risks

## 14. Success Criteria
"""


def generate_brd(source_text: str) -> str:
    """Phase 1: Send raw extracted text to LLM, return BRD markdown."""
    if not source_text or not source_text.strip():
        raise ValueError("Source text is empty. Cannot generate BRD.")
    return _call_with_retry(_BRD_SYSTEM_PROMPT, f"Source Document:\n\n{source_text}")


def generate_final_brd(aggregated_text: str) -> str:
    """Phase 3: Send aggregated intermediate information to LLM, return final BRD markdown."""
    if not aggregated_text or not aggregated_text.strip():
        raise ValueError("Aggregated text is empty. Cannot generate final BRD.")
    return _call_with_retry(_FINAL_BRD_SYSTEM_PROMPT, f"Aggregated Requirements Information:\n\n{aggregated_text}")


def _call_with_retry(system_prompt: str, user_content: str, retries: int = 3) -> str:
    """Call LLM with retry on None/empty response."""
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    last_error = None
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                max_tokens=8000,
                timeout=120,
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return _clean_response(content)
            print(f"  [WARNING] BRD generation attempt {attempt+1} returned empty, retrying...")
            time.sleep(3)
        except Exception as e:
            last_error = e
            print(f"  [WARNING] BRD generation attempt {attempt+1} failed: {e}")
            time.sleep(3)
    raise ValueError(f"LLM returned empty response after {retries} attempts. Last error: {last_error}")


def _clean_response(content: str) -> str:
    """Strip reasoning preamble — keep only from the first # heading onward."""
    idx = content.find("# Business Requirements Document")
    if idx != -1:
        return content[idx:].strip()
    idx = content.find("#")
    if idx != -1:
        return content[idx:].strip()
    return content.strip()
