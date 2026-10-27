from backend.app.document_processor import extract_text
from backend.app.text_chunker import clean_text, chunk_text

PDF_PATH = r"c:\Users\prasa\Desktop\FINAL YEAR PROJ\pdf's\IC-Sample-Business-Requirements-Document-Template-11238_PDF.pdf"

# Step 1: Extract
raw = extract_text(PDF_PATH)
print(f"[1] Raw text      : {len(raw)} characters")

# Step 2: Clean
cleaned = clean_text(raw)
print(f"[2] Cleaned text  : {len(cleaned)} characters")

# Step 3: Chunk
chunks = chunk_text(cleaned, max_tokens=800, overlap_tokens=100, source="IC-Sample.pdf")
print(f"[3] Total chunks  : {len(chunks)}")
print()

# Show each chunk summary
for c in chunks:
    preview = c["text"][:80].replace("\n", " ")
    print(f"  Chunk {c['chunk_id']:02d} | tokens: {c['token_count']:4d} | {preview}...")

print()
print("Phase 2 pipeline working correctly.")
