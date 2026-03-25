"""
clean_training.py
=================
Preprocessing pipeline for CBLM Social Compliance & Environmental Management
Workflow: PDF → Text Extraction → Cleaning → Chunking → Save

Source : Final_CBLM-Social-Com-Env-Mgt_23-Nov-25_1766467717618.pdf
         (299-page official RMG sector training manual — social compliance,
          labor rights, environmental management, safety)
Pages  : 299 total | skip first 2 (cover + module index table)
Output : processed/training_chunks.txt
"""

import re
import os
import fitz  # PyMuPDF

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
PDF_PATH   = "raw/Final_CBLM-Social-Com-Env-Mgt_23-Nov-25_1766467717618.pdf"
OUTPUT_TXT = "processed/training_chunks.txt"
SOURCE     = "Training"
CHUNK_SIZE = 1000
OVERLAP    = 100

# Pages to skip (0-indexed):
#   0   = cover page
#   1   = module instruction index table
SKIP_PAGES = {0, 1}

# ─────────────────────────────────────────────
# STEP 1: EXTRACT TEXT
# ─────────────────────────────────────────────
print("=" * 60)
print(f"Preprocessing: {SOURCE}")
print("=" * 60)
print("\n[1/4] Extracting text from PDF...")

doc = fitz.open(PDF_PATH)
total_pages = len(doc)
parts, kept_pages = [], []

for i, page in enumerate(doc):
    if i in SKIP_PAGES:
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
    # Remove running header "Social Compliance & Environmental Management"
    text = re.sub(r'Social Compliance\s*[&\u0026]\s*Environmental Management\s*\n?',
                  '', text, flags=re.IGNORECASE)

    # Remove standalone page numbers
    text = re.sub(r'^\s*\d{1,3}\s*$', '', text, flags=re.MULTILINE)

    # Remove "Page X of Y" patterns
    text = re.sub(r'Page\s+\d+\s*(of\s+\d+)?', '', text, flags=re.IGNORECASE)

    # Remove URLs
    text = re.sub(r'(https?://|www\.)\S+', '', text)

    # Remove non-ASCII
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Remove separator lines
    text = re.sub(r'[-=_]{3,}', '', text)
    text = re.sub(r'\.{4,}', '', text)

    # Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Drop very short noise lines
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
