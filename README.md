# Knowledge Base – Data Preprocessing

Project: AI-Based Knowledge Management System for Garment Factories

## Folder Structure

```
Experiment/
├── chunked-data/           ← Generated *_chunks.txt and *_manifest.json (submit the .txt)
├── chunked-data-code/      ← chunk_markdown_langchain.py (markdown → chunks)
├── md data/                ← Markdown sources (after PDF conversion)
├── raw-data/               ← Original PDFs and other binaries
├── requirements.txt        ← pip deps (e.g. langchain-text-splitters)
├── knowledge_base/         ← Final merged knowledge base (Week 5+)
└── README.md
```

## Chunking from Markdown (current)

Install and run from the **repository root**:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python chunked-data-code/chunk_markdown_langchain.py \
  --input "md data/your_file.md" \
  --source-name "Your source label" \
  --document-name "Human-readable document title"
```

Optional flags: `--chunk-size`, `--chunk-overlap`, `--min-chunk-chars`, `--write-raw-chunks`, `--output-dir` (defaults to `chunked-data/` at repo root). By default the script strips repeated PDF-style lines (running title + standalone page numbers); use `--keep-running-title` or `--keep-page-numbers` to disable that for other corpora.

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

## Team Commands

| Member | Data Source | Command |
|---|---|---|
| Member 2 | Fire Safety PDF | `python scripts/preprocess.py --input raw/RSC-Fire-Safety-Manual-for-RMG-Buildings.pdf --source "Fire Safety" --skip_first 3 --skip_last 1 --skip_ranges 26-42` |
| Member 3 | Labour Law PDF | `python scripts/preprocess.py --input raw/labour_law.pdf --source "Labour Law" --skip_first 2 --skip_last 1` |
| Member 4 | Sewing Machine Manual | `python scripts/preprocess.py --input raw/machine_manual.pdf --source "Machine Manual" --skip_first 1` |
| Member 5 | SOP Document | `python scripts/preprocess.py --input raw/sop.pdf --source "SOP" --skip_first 1` |

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
