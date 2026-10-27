# AI-Powered BRD Generation System

## Project Objective

Automatically generate a structured Business Requirements Document (BRD) from unstructured business input (PDF or TXT) using an LLM.

---

## Phase 1 Scope

- Accept PDF or TXT input files
- Extract text using PyMuPDF or standard file I/O
- Send extracted text to OpenAI GPT-4o
- Generate a structured BRD in Markdown format
- Save output to `data/output/`

---

## Architecture

```
Input File (PDF/TXT)
        ↓
document_processor.py  →  extract_text()
        ↓
brd_generator.py       →  generate_brd()  →  OpenAI API
        ↓
main.py                →  save BRD to data/output/
        ↓
BRD_{filename}_{timestamp}.md
```

---

## Technologies Used

| Library | Purpose |
|---|---|
| PyMuPDF (`fitz`) | PDF text extraction |
| `openai` | LLM API client |
| `python-dotenv` | Load API key from `.env` |
| `pytest` | Unit testing |

---

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd ai-brd-generator

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Environment Variable Setup

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o
```

Never commit `.env` to version control. It is already listed in `.gitignore`.

---

## Providing an Input Document

Place your PDF or TXT file inside `data/input/`:

```
data/input/my_requirements.pdf
data/input/my_requirements.txt
```

---

## Running the Application

From the `ai-brd-generator/` directory:

```bash
python -m backend.app.main data/input/my_requirements.pdf
```

or for a TXT file:

```bash
python -m backend.app.main data/input/my_requirements.txt
```

The generated BRD will be printed to the terminal and saved to `data/output/`.

---

## Running Tests

```bash
pytest
```

All tests mock the LLM — no API key is required to run tests.

---

## Example Output

```markdown
# Business Requirements Document

## 1. Project Title
Customer Order Management Portal

## 2. Executive Summary
The project aims to build a web-based portal...

## 7. Functional Requirements
FR-01: Users shall be able to register and log in.
FR-02: Users shall be able to view order history.

...
```

---

## Current Limitations

- Single document input only (no multi-document processing)
- No document chunking — input must fit within the LLM context window (~128k tokens for GPT-4o)
- Output format: Markdown only
- No web interface

---

## Planned Future Phases

| Phase | Feature |
|---|---|
| Phase 2 | Document chunking for large files |
| Phase 3 | Multi-document processing |
| Phase 4 | RAG with vector database |
| Phase 5 | Faithfulness / hallucination checking |
| Phase 6 | FastAPI backend + React frontend |
| Phase 7 | Authentication and deployment |
