import os
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from backend.app.config import validate_config, OUTPUT_DIR
from backend.app.document_processor import extract_text, SUPPORTED_EXTENSIONS
from backend.app.text_chunker import clean_text, chunk_text, count_tokens
from backend.app.hierarchical_processor import extract_from_chunk, aggregate, format_for_final_generation
from backend.app.brd_generator import generate_brd, generate_final_brd

try:
    from backend.app.pdf_generator import markdown_to_pdf
    PDF_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] PDF generation unavailable: {e}")
    PDF_AVAILABLE = False

CHUNK_THRESHOLD_TOKENS = 800

app = FastAPI(title="BRD Generator API")

# Middleware must be registered before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.get("/health")
def health():
    return {"status": "ok", "pdf_available": PDF_AVAILABLE}


@app.post("/generate-brd")
async def generate_brd_endpoint(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Supported: PDF, TXT")

    try:
        validate_config()
    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=str(e))

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        raw_text = extract_text(tmp_path)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=422, detail=str(e))

    os.unlink(tmp_path)

    cleaned_text = clean_text(raw_text)
    total_tokens = count_tokens(cleaned_text)

    try:
        if total_tokens <= CHUNK_THRESHOLD_TOKENS:
            brd = generate_brd(cleaned_text)
        else:
            chunks = chunk_text(cleaned_text, max_tokens=800, overlap_tokens=100, source=file.filename)
            chunk_results = [extract_from_chunk(chunk) for chunk in chunks]
            aggregated = aggregate(chunk_results)
            aggregated_text = format_for_final_generation(aggregated)
            brd = generate_final_brd(aggregated_text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BRD generation failed: {str(e)}")

    return JSONResponse({"brd": brd, "filename": file.filename})


@app.post("/download-pdf")
async def download_pdf(brd: str = Form(...), filename: str = Form(...)):
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF generation unavailable. Install reportlab.")
    try:
        pdf_bytes = markdown_to_pdf(brd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    pdf_name = f"BRD_{filename.rsplit('.', 1)[0]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf_name}"'},
    )
