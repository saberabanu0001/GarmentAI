# Knowledge Base – Data Preprocessing

Project: AI-Based Knowledge Management System for Garment Factories

## Folder Structure

```
Experiment/
├── chunked-data/           ← Generated *_chunks.txt and *_manifest.json (submit the .txt)
├── chunked-data-code/      ← data-named scripts + markdown_langchain_chunker.py (engine)
├── md data/                ← Markdown sources (after PDF conversion)
├── raw-data/               ← Original PDFs and other binaries
├── requirements.txt        ← pip deps (e.g. langchain-text-splitters)
├── embedding/              ← build_index / build_chroma, numpy + Chroma query CLIs, search_web; see below
├── knowledge_base/         ← Final merged knowledge base (Week 5+)
└── README.md
```

## Embeddings (multilingual E5)

Uses **`intfloat/multilingual-e5-small`** (384-dim): `passage:` for chunks, `query:` at search time (works for Bangla or English queries).

```bash
pip install -r requirements.txt
python embedding/build_index.py              # reads chunked-data/*_chunks.txt
python embedding/query_engine.py "your question" --top-k 5   # bridge: query → vectors → top chunks
# or: python embedding/search_cli.py "your question" --top-k 5
python embedding/search_web.py                    # http://127.0.0.1:8765
python embedding/search_web.py --port 8766        # if 8765 is already in use
```

**Query engine:** `embedding/query_engine.py` loads the index, embeds the user string with `query:`, scores against `embeddings.npy`, returns top‑k hits. Use `--json` for machine-readable output. **`embedding/search_web.py`** is a tiny browser UI for manual testing (127.0.0.1 only).

Outputs: `embedding/index/embeddings.npy`, `chunks.jsonl`, `meta.json`. Models cache under `embedding/.hf_cache/`.

Build options: `--model intfloat/multilingual-e5-base`, `--batch-size`, `--chunks-dir`, `--output-dir`.

### ChromaDB (multi-collection + RBAC)

Collections and metadata are driven by [`embedding/collection_manifest.yaml`](embedding/collection_manifest.yaml) (filename patterns → `global_laws`, `compliance_standards`, `factory_{slug}_docs`). Canonical role strings live in [`embedding/roles.py`](embedding/roles.py). Each chunk gets a stable `chunk_uid` and fields such as `doc_scope`, `language` (`en` / `bn`), and `allowed_roles` (comma-separated in Chroma).

```bash
python embedding/build_chroma.py                    # writes embedding/chroma_data/ (ignored by git)
python embedding/chroma_query_engine.py "fire exit" --role worker --factory good --top-k 5
python embedding/chroma_query_engine.py "salary deduction" --role hr_staff --factory risky --json
```

Merge policy: sort by **similarity** (cosine via Chroma space), then tie-break **tenant → compliance → global law**. Post-filter drops chunks the `role` is not allowed to see (e.g. HR-only dummy corpus under `factory_risky_docs`).

**Tests:** `pytest tests/test_embedding_rbac.py` (fast). After building Chroma: `RUN_E2E=1 pytest tests/test_chroma_e2e.py -m e2e` (RBAC + Bangla smoke).

Dummy tenant seed files for Month 2: [`chunked-data/factory_good_dummy_chunks.txt`](chunked-data/factory_good_dummy_chunks.txt), [`chunked-data/factory_risky_dummy_chunks.txt`](chunked-data/factory_risky_dummy_chunks.txt).

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
1. The combined `.txt` file from `chunked-data/` (e.g. `*_chunks.txt`), or from `processed/` if using a legacy pipeline
2. Source name
3. Number of chunks (shown at end of script output)

## Workflow

```
Document → Text Extraction → Cleaning → Chunking → processed/*.txt → Knowledge Base
```
