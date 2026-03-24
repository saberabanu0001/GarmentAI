# Knowledge Base – Data Preprocessing

Project: AI-Based Knowledge Management System for Garment Factories

## Folder Structure

```
data/
├── raw/                  ← Original source files (PDFs, docx, HTML)
├── processed/            ← Output chunk .txt files (submit these)
├── scripts/              ← Preprocessing scripts
│   ├── preprocess.py     ← General-purpose script (use this for new sources)
│   └── clean_fire_safety.py  ← Fire Safety specific script (v2)
├── knowledge_base/       ← Final merged knowledge base (Week 5+)
└── README.md
```

## How to Preprocess a New PDF

Run from the `data/` folder:

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

---

## Team Commands

| Member | Data Source | Command |
|---|---|---|
| Member 2 | Fire Safety PDF | `python scripts/preprocess.py --input raw/RSC-Fire-Safety-Manual-for-RMG-Buildings.pdf --source "Fire Safety" --skip_first 3 --skip_last 1 --skip_ranges 26-42` |
| Member 3 | Labour Law PDF | `python scripts/preprocess.py --input raw/labour_law.pdf --source "Labour Law" --skip_first 2 --skip_last 1` |
| Member 4 | Sewing Machine Manual | `python scripts/preprocess.py --input raw/machine_manual.pdf --source "Machine Manual" --skip_first 1` |
| Member 5 | SOP Document | `python scripts/preprocess.py --input raw/sop.pdf --source "SOP" --skip_first 1` |

---

## What to Submit

Each member sends:
1. The `.txt` file from `processed/` folder
2. Source name
3. Number of chunks (shown at end of script output)

## Workflow

```
Document → Text Extraction → Cleaning → Chunking → processed/*.txt → Knowledge Base
```
