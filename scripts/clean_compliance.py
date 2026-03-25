"""
clean_compliance.py
===================
Preprocessing pipeline for Compliance Guidelines (amfori BSCI website)
Workflow: Text Input → Cleaning → Chunking → Save

Source : https://www.amfori.org/amfori-bsci/
Method : Paste the copied website text into the TEXT variable below

Instructions:
  1. Open https://www.amfori.org/amfori-bsci/ in your browser
  2. Select all main content text (skip navigation/footer)
  3. Copy it (Ctrl+C)
  4. Paste it into TEXT = \"\"\" ... \"\"\" below
  5. Run: python scripts/clean_compliance.py
"""

import re
import os

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
OUTPUT_TXT = "processed/compliance_chunks.txt"
SOURCE     = "Compliance"
CHUNK_SIZE = 1000
OVERLAP    = 100

# ─────────────────────────────────────────────
# PASTE YOUR COPIED WEBSITE TEXT HERE
# ─────────────────────────────────────────────
TEXT = """
Paste the amfori BSCI compliance guidelines text here.
Replace this entire block with the actual copied text.
"""

# ─────────────────────────────────────────────
# STEP 2: CLEAN TEXT
# ─────────────────────────────────────────────
print("=" * 60)
print(f"Preprocessing: {SOURCE}")
print("=" * 60)
print("\n[2/4] Cleaning text...")

def clean_text(text):
    # Remove navigation-style short lines (menu items etc.)
    text = re.sub(r'^\s*(Home|Menu|Skip|Login|Register|Search|Cookie|Privacy|Terms)[^\n]*\n',
                  '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'(https?://|www\.)\S+', '', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'[-=_]{3,}', '', text)
    text = re.sub(r'\.{4,}', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [ln for ln in text.split('\n') if len(ln.strip()) >= 3 or ln.strip() == '']
    return '\n'.join(lines).strip()

raw_text = TEXT.strip()
cleaned = clean_text(raw_text)
removed = len(raw_text) - len(cleaned)
print(f"  Raw chars  : {len(raw_text):,}")
print(f"  Clean chars: {len(cleaned):,}  (removed {removed:,})")

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
    f.write(f"URL     : https://www.amfori.org/amfori-bsci/\n")
    f.write(f"CHUNKS  : {len(chunks)}  | Size: {CHUNK_SIZE}  | Overlap: {OVERLAP}\n")
    f.write("=" * 60 + "\n\n")
    for i, chunk in enumerate(chunks, 1):
        f.write(f"[CHUNK {i}]\n{chunk}\n\n")

size_kb = os.path.getsize(OUTPUT_TXT) / 1024
print(f"  Saved: {OUTPUT_TXT}  ({size_kb:.1f} KB)")
print("\n" + "=" * 60)
print(f"  DONE → {os.path.basename(OUTPUT_TXT)} | {SOURCE} | {len(chunks)} chunks")
print("=" * 60 + "\n")
