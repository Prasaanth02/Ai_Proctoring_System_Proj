import os
import sys
from datetime import datetime

from backend.app.config import validate_config, OUTPUT_DIR
from backend.app.document_processor import extract_text
from backend.app.text_chunker import clean_text, chunk_text, count_tokens
from backend.app.hierarchical_processor import (
    extract_from_chunk,
    aggregate,
    format_for_final_generation,
)
from backend.app.brd_generator import generate_brd, generate_final_brd

# Documents under this token count go through Phase 1 (single-shot).
# Documents over this threshold go through Phase 3 (hierarchical).
CHUNK_THRESHOLD_TOKENS = 800


def save_brd(brd_content: str, input_file: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"BRD_{base_name}_{timestamp}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(brd_content)
    return output_path


def run(input_file: str):
    validate_config()

    # ── Step 1: Extract ──────────────────────────────────────────────────────
    print(f"[1/5] Extracting text from: {input_file}")
    raw_text = extract_text(input_file)
    print(f"      Extracted {len(raw_text)} characters.\n")

    # ── Step 2: Clean ────────────────────────────────────────────────────────
    print("[2/5] Cleaning text...")
    cleaned_text = clean_text(raw_text)
    total_tokens = count_tokens(cleaned_text)
    print(f"      {len(cleaned_text)} characters | {total_tokens} tokens.\n")

    # ── Step 3: Route — single-shot or hierarchical ──────────────────────────
    if total_tokens <= CHUNK_THRESHOLD_TOKENS:
        print("[3/5] Document fits in one chunk — using single-shot generation (Phase 1 path).\n")
        print("[4/5] Generating BRD via LLM...")
        brd = generate_brd(cleaned_text)
        print("      Done.\n")
    else:
        print("[3/5] Chunking document...")
        chunks = chunk_text(
            cleaned_text,
            max_tokens=800,
            overlap_tokens=100,
            source=os.path.basename(input_file),
        )
        print(f"      {len(chunks)} chunks created.\n")

        print("[4/5] Processing chunks hierarchically...")
        chunk_results = []
        for chunk in chunks:
            print(f"      Chunk {chunk['chunk_id']}/{len(chunks)} ({chunk['token_count']} tokens)...")
            result = extract_from_chunk(chunk)
            chunk_results.append(result)

        print("\n      Aggregating results...")
        aggregated = aggregate(chunk_results)

        fr_count = len(aggregated["functional_requirements"])
        nfr_count = len(aggregated["non_functional_requirements"])
        print(f"      Aggregated: {fr_count} functional, {nfr_count} non-functional requirements.\n")

        print("      Generating final BRD from aggregated information...")
        aggregated_text = format_for_final_generation(aggregated)
        brd = generate_final_brd(aggregated_text)
        print("      Done.\n")

    # ── Step 5: Save ─────────────────────────────────────────────────────────
    print("[5/5] Saving output...")
    output_path = save_brd(brd, input_file)
    print(f"      Saved to: {output_path}\n")

    print("=" * 60)
    print(brd.encode("cp1252", errors="replace").decode("cp1252"))
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m backend.app.main <path_to_input_file>")
        sys.exit(1)
    run(sys.argv[1])
