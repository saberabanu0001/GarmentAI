"""
clean_sop.py
============
Preprocessing pipeline for SOP (Standard Operating Procedures) Document
Workflow: PDF → Text Extraction → Cleaning → Chunking → Save

Source : Add your SOP PDF to raw/ folder and update PDF_PATH below
Output : processed/sop_chunks.txt

Instructions:
  1. Download your SOP PDF and place it in the raw/ folder
  2. Update PDF_PATH below with the correct filename
  3. Adjust SKIP_FIRST / SKIP_LAST / SKIP_PAGES if needed
  4. Run: python scripts/clean_sop.py
"""

import re
import os
import fitz  # PyMuPDF

# ─────────────────────────────────────────────
# CONFIGURATION  ← Update these if needed
# ─────────────────────────────────────────────
PDF_PATH   = "raw/sop.pdf"          # ← change to your actual filename
OUTPUT_TXT = "processed/sop_chunks.txt"
SOURCE     = "SOP"
CHUNK_SIZE = 1000
OVERLAP    = 100

# Pages to skip (0-indexed):
SKIP_FIRST = 1   # skip cover page
SKIP_LAST  = 0   # skip last N pages (e.g. contact/colophon)
# Add any middle ranges to skip (e.g. appendix forms) as 0-indexed page sets:
SKIP_EXTRA = set()   # e.g. set(range(20, 30))

# ─────────────────────────────────────────────
# STEP 1: EXTRACT TEXT
# ─────────────────────────────────────────────
print("=" * 60)
print(f"Preprocessing: {SOURCE}")
print("=" * 60)
print("\n[1/4] Extracting text from PDF...")

if not os.path.isfile(PDF_PATH):
    print(f"\n❌ File not found: {PDF_PATH}")
    print("   Please add your SOP PDF to the raw/ folder and update PDF_PATH.")
    exit(1)

doc = fitz.open(PDF_PATH)
total_pages = len(doc)

skip_pages = set(range(0, SKIP_FIRST))
skip_pages.update(range(total_pages - SKIP_LAST, total_pages))
skip_pages.update(SKIP_EXTRA)

parts, kept_pages = [], []
for i, page in enumerate(doc):
    if i in skip_pages:
        continue
    text = page.get_text()
    if text.strip():
        parts.append(text)
        kept_pages.append(i + 1)

doc.close()
raw_text = "\n".join(parts)
print(f"  Pages kept : {len(kept_pages)} / {total_pages}")
print(f"  Raw chars  : {len(raw_text):,}")

# ─────────────────────────────────────────────
# STEP 2: CLEAN TEXT
# ─────────────────────────────────────────────
print("\n[2/4] Cleaning text...")

def clean_text(text):
    text = re.sub(r'^\s*\d{1,3}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'Page\s+\d+\s*(of\s+\d+)?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(https?://|www\.)\S+', '', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'[-=_]{3,}', '', text)
    text = re.sub(r'\.{4,}', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [ln for ln in text.split('\n') if len(ln.strip()) >= 3 or ln.strip() == '']
    return '\n'.join(lines).strip()

cleaned = clean_text(raw_text)
removed = len(raw_text) - len(cleaned)
print(f"  Clean chars: {len(cleaned):,}  (removed {removed:,} = {removed/len(raw_text)*100:.1f}%)")

# ─────────────────────────────────────────────
# STEP 3: CHUNK TEXT
# ─────────────────────────────────────────────
print("\n[3/4] Chunking...")

def chunk_text(text, chunk_size=1000, overlap=100):
    chunks = []
    length = len(text)
    pos = 0
    min_step = chunk_size - overlap

    while pos < length:
        end = min(pos + chunk_size, length)
        if end >= length:
            chunk = text[pos:].strip()
            if chunk:
                chunks.append(chunk)
            break

        search_start = pos + max(min_step // 2, 1)
        para = text.rfind('\n\n', search_start, end)
        sent = max(text.rfind('. ', search_start, end),
                   text.rfind('.\n', search_start, end))
        nl   = text.rfind('\n', search_start, end)

        if para > 0:     boundary = para
        elif sent > 0:   boundary = sent + 1
        elif nl > 0:     boundary = nl
        else:            boundary = end

        chunk = text[pos:boundary].strip()
        if chunk:
            chunks.append(chunk)

        pos = boundary - overlap
        if pos <= 0:
            pos = boundary

    return chunks

chunks = chunk_text(cleaned, CHUNK_SIZE, OVERLAP)
avg = sum(len(c) for c in chunks) // max(len(chunks), 1)
print(f"  Total chunks: {len(chunks)}")
print(f"  Avg length  : {avg} chars")

# ─────────────────────────────────────────────
# STEP 4: SAVE OUTPUT
# ─────────────────────────────────────────────
print("\n[4/4] Saving output...")
os.makedirs("processed", exist_ok=True)

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write(f"SOURCE  : {SOURCE}\n")
    f.write(f"FILE    : {os.path.basename(PDF_PATH)}\n")
    f.write(f"PAGES   : {len(kept_pages)} kept of {total_pages} total\n")
    f.write(f"CHUNKS  : {len(chunks)}  | Size: {CHUNK_SIZE}  | Overlap: {OVERLAP}\n")
    f.write("=" * 60 + "\n\n")
    for i, chunk in enumerate(chunks, 1):
        f.write(f"[CHUNK {i}]\n{chunk}\n\n")

size_kb = os.path.getsize(OUTPUT_TXT) / 1024
print(f"  Saved: {OUTPUT_TXT}  ({size_kb:.1f} KB)")
print("\n" + "=" * 60)
print(f"  DONE → {os.path.basename(OUTPUT_TXT)} | {SOURCE} | {len(chunks)} chunks")
print("=" * 60 + "\n")
