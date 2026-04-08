# Garment-AI (Garment Factory Knowledge System)

AI-based knowledge management: multilingual **E5** retrieval in **Chroma**, **RBAC**, **RAG** (FastAPI + optional Ollama / Groq / Gemini), and a **Next.js** UI.

## Repository layout

```
Experiment/   (or rename clone to garment-ai/)
├── .env                  # Secrets — never commit (see .env.example)
├── backend/              # FastAPI app
│   ├── main.py
│   ├── core/             # config.py, security.py (Role + RBAC helpers)
│   ├── api/              # chat.py, audit.py, documents.py
│   ├── services/         # chroma_engine, embedder, llm_wrapper, rag, chroma_ingest, hr_data
│   └── collection_manifest.yaml
├── frontend/             # Next.js + TypeScript
├── data/
│   ├── raw/                # Original PDFs (optional; team may use raw-data/)
│   ├── chunked/            # *_chunks.txt + manifests (ingest input)
│   ├── dummy/              # Placeholder for synthetic worker profiles
│   ├── chroma_data/        # Local Chroma DB (gitignored; built at runtime)
│   ├── hr_dashboard.example.json   # Template for HR dashboard JSON
│   └── hr_dashboard.json   # Created by HR UI (PUT); gitignored — factory-specific
├── scripts/
│   ├── ingest_laws.py      # Build / refresh Chroma from data/chunked
│   └── seed_dummy_data.py  # Stub for future dummy seeding
├── embedding/              # Thin shims → backend.* (legacy CLI paths)
├── tests/                  # pytest: test_rbac.py, test_rag_flow.py, test_chroma_e2e.py
├── chunked-data-code/      # Chunk drivers + markdown_langchain_chunker.py
├── md data/                # Markdown sources
├── raw-data/               # Original PDFs (existing team folder)
├── requirements.txt
└── README.md
```

**Flow:** **`frontend/`** calls **`backend/`** over HTTP. Chunk scripts write to **`data/chunked`**; **`python scripts/ingest_laws.py`** embeds into **`data/chroma_data/`**. **`embedding/`** re-exports **`backend`** so older commands like **`python embedding/rag_cli.py`** still work.

## Embeddings (multilingual E5)

Uses **`intfloat/multilingual-e5-small`** (384-dim): `passage:` for chunks, `query:` at search time (works for Bangla or English queries).

```bash
pip install -r requirements.txt
python embedding/build_index.py              # reads data/chunked/*_chunks.txt
python embedding/query_engine.py "your question" --top-k 5   # bridge: query → vectors → top chunks
# or: python embedding/search_cli.py "your question" --top-k 5
python embedding/search_web.py                    # http://127.0.0.1:8765
python embedding/search_web.py --port 8766        # if 8765 is already in use
```

**Query engine:** `embedding/query_engine.py` loads the index, embeds the user string with `query:`, scores against `embeddings.npy`, returns top‑k hits. Use `--json` for machine-readable output. **`embedding/search_web.py`** is a tiny browser UI for manual testing (127.0.0.1 only).

Outputs: `embedding/index/embeddings.npy`, `chunks.jsonl`, `meta.json`. Hugging Face cache defaults under `data/.hf_cache/` (via backend embedder).

Build options: `--model intfloat/multilingual-e5-base`, `--batch-size`, `--chunks-dir`, `--output-dir`.

### ChromaDB (multi-collection + RBAC)

Collections and metadata are driven by [`backend/collection_manifest.yaml`](backend/collection_manifest.yaml). Canonical role strings live in [`backend/core/security.py`](backend/core/security.py) (also re-exported as [`embedding/roles.py`](embedding/roles.py)). Each chunk gets a stable `chunk_uid` and fields such as `doc_scope`, `language` (`en` / `bn`), and `allowed_roles` (comma-separated in Chroma).

```bash
python scripts/ingest_laws.py                       # writes data/chroma_data/ (gitignored)
python embedding/build_chroma.py                    # same as ingest_laws (compat)
python embedding/chroma_query_engine.py "fire exit" --role worker --factory good --top-k 5
python embedding/chroma_query_engine.py "salary deduction" --role hr_staff --factory risky --json
```

Merge policy: sort by **similarity** (cosine via Chroma space), then tie-break **tenant → compliance → global law**. Post-filter drops chunks the `role` is not allowed to see (e.g. HR-only dummy corpus under `factory_risky_docs`).

**Tests:** `pytest tests/test_rbac.py` (fast). After building Chroma: `RUN_E2E=1 pytest tests/test_chroma_e2e.py -m e2e` (RBAC + Bangla smoke). API smoke: `pytest tests/test_rag_flow.py`.

Dummy tenant seed files: [`data/chunked/factory_good_dummy_chunks.txt`](data/chunked/factory_good_dummy_chunks.txt), [`data/chunked/factory_risky_dummy_chunks.txt`](data/chunked/factory_risky_dummy_chunks.txt).

### LLM: Ollama (daily dev) vs Groq (final demo)

- **Ollama** — free, local, good for team coding. Install models once; keep `ollama serve` running (often automatic on macOS).
- **Groq** — fast hosted inference for demos; model **`llama-3.3-70b-versatile`**. Get an API key at [Groq Cloud](https://console.groq.com/). Never commit keys; use `.env` (see [`.env.example`](.env.example)).

**1. Ollama setup (each machine / once per model)**

```bash
ollama pull llama3.2
# Stronger multilingual answers (optional, larger download):
# ollama pull qwen2.5:7b
curl -s http://127.0.0.1:11434/api/tags   # confirm daemon sees models
pip install -r requirements.txt
export LLM_BACKEND=ollama
export OLLAMA_MODEL=llama3.2
python scripts/ingest_laws.py   # if not already built
python embedding/rag_cli.py "What is weekly holiday for workers?" --role worker
```

**2. Groq setup (demo day)**

```bash
export GROQ_API_KEY="gsk_..."
export LLM_BACKEND=groq
export GROQ_MODEL=llama-3.3-70b-versatile
python embedding/rag_cli.py "Summarise compensatory weekly holiday." --role worker --backend groq
```

RAG stack: **`backend/services/rag.py`** (retrieve from Chroma → prompt) and **`backend/services/llm_wrapper.py`** (Ollama / Groq / Gemini). Legacy imports: **`embedding/rag_answer.py`**, **`embedding/llm_client.py`**.

### GarmentAI UI (Next.js + TypeScript)

**Worker** (RAG → `POST /api/chat`), **HR** dashboard (`GET /api/hr/dashboard`), **Auditor** shells. Optional hooks under `frontend/src/hooks/`.

**1. API (FastAPI, CORS open for local dev)**

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 5050
# POST /api/chat  JSON: { "question", "role", "factory_id?", "top_k?", "backend?" }
# POST /api/rag   — same body (legacy alias)
```

Shortcut: `python embedding/garment_api.py` (uvicorn on port 5050).

**2. Front end**

```bash
cd frontend
cp .env.example .env.local   # optional; NEXT_PUBLIC_API_URL=http://127.0.0.1:5050
npm install
npm run dev                   # http://localhost:3000
```

Production: tighten CORS in `backend/main.py` and restrict origins.

## Chunking from Markdown (current)

Install and run from the **repository root**:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### By data file name (recommended)

| Markdown source | Chunk script |
|-----------------|--------------|
| `md data/1 labour law 2006 data.md` | `python chunked-data-code/labour_law_2006_data_chunk.py` |
| `md data/1.1 labour law 2015.md` | `python chunked-data-code/labour_law_2015_data_chunk.py` |
| `md data/2 fire safety data.md` | `python chunked-data-code/fire_safety_data_chunk.py` |
| `md data/3 compliance garment dhaka data.md` | `python chunked-data-code/compliance_garment_dhaka_data_chunk.py` |
| `md data/4 CBLM social compliance data.md` | `python chunked-data-code/cblm_social_compliance_data_chunk.py` |
| `md data/5 JUKI machine manual data.md` | `python chunked-data-code/juki_machine_manual_data_chunk.py` |
| `md data/6 term project description data.md` | `python chunked-data-code/term_project_description_data_chunk.py` |

Optional extra flags (appended): `--chunk-size`, `--chunk-overlap`, `--min-chunk-chars`, `--write-raw-chunks`, `--output-dir`. Defaults strip PDF-style noise (running title + page numbers); use `--keep-running-title` or `--keep-page-numbers` when needed.

### PDF → Markdown (pymupdf4llm), by data name

| Output markdown | Script (defaults match paths below) |
|-----------------|-------------------------------------|
| `md data/1 labour law 2006 data.md` | `python chunked-data-code/labour_law_2006_data_pdf_to_markdown.py` |
| `md data/1.1 labour law 2015.md` | `python chunked-data-code/labour_law_2015_data_pdf_to_markdown.py` |
| `md data/2 fire safety data.md` | `python chunked-data-code/fire_safety_data_pdf_to_markdown.py` |
| `md data/3 compliance garment dhaka data.md` | `python chunked-data-code/compliance_garment_dhaka_data_pdf_to_markdown.py` |
| `md data/4 CBLM social compliance data.md` | `python chunked-data-code/cblm_social_compliance_data_pdf_to_markdown.py` |
| `md data/5 JUKI machine manual data.md` | `python chunked-data-code/juki_machine_manual_data_pdf_to_markdown.py` |
| `md data/6 term project description data.md` | `python chunked-data-code/term_project_description_data_pdf_to_markdown.py` |

Each accepts `--input` and `--output` to override the default PDF and `.md` paths.

`Instructions for Data Pre-processing.docx` is not handled here (Word); convert to `.md` yourself if you need it in the pipeline.

### Generic chunker (any other `.md`)

```bash
python chunked-data-code/markdown_langchain_chunker.py \
  --input "md data/your_file.md" \
  --source-name "Your source label" \
  --document-name "Human-readable document title"
```

## Standard Output Contract

All generated files now use one shared format:

```text
DOCUMENT_METADATA
source_name: ...
document_name: ...
...

--- CHUNK START ---
chunk_id: ...
document_name: ...
source_name: ...
page_start: ...
page_end: ...
section: ...
text:
...
--- CHUNK END ---
```

Each chunk carries its own metadata so the downstream RAG pipeline can parse every file the same way.

## Legacy: PDF preprocessing (not in this repo layout)

If you still use a PDF-based script, run it from the folder that contains `scripts/`:


```bash
python scripts/preprocess.py \
  --input raw/YOUR_FILE.pdf \
  --source "Your Source Name" \
  --skip_first 3 \
  --skip_last 1 \
  --skip_ranges 26-42 \
  --chunk_size 1000
```

### Arguments

| Argument | Description | Default |
|---|---|---|
| `--input` | Path to PDF file | required |
| `--source` | Name for this data source | required |
| `--skip_first N` | Skip first N pages (cover, TOC) | 0 |
| `--skip_last N` | Skip last N pages (colophon) | 0 |
| `--skip_ranges A-B` | Skip page ranges (e.g. appendix forms) | none |
| `--chunk_size` | Target characters per chunk | 1000 |
| `--overlap` | Overlap chars between chunks | 100 |
| `--output_name` | Optional output filename override | auto |

---

## Notes

The shared pipeline now:

1. Removes repeated headers/footers and common extraction noise such as timestamps and site banners.
2. Preserves overlap while aligning new chunks to cleaner boundaries so they do not start mid-word when possible.
3. Records `document_name`, `chunk_id`, `page_start`, `page_end`, and a best-effort `section` for every chunk.

## What to Submit

Each member sends:
1. The combined `.txt` file from `data/chunked/` (e.g. `*_chunks.txt`), or from `processed/` if using a legacy pipeline
2. Source name
3. Number of chunks (shown at end of script output)

## Workflow

```
Document → Text Extraction → Cleaning → Chunking → processed/*.txt → Knowledge Base
```
