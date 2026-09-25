#!/usr/bin/env python3
"""
NyayaPath — Bare Act Ingestion Script

Parses plain-text bare act files, splits them by section, and indexes
them into the ChromaDB + BM25 hybrid retrieval store.

Usage:
    # Place your bare-act .txt files in data/bare_acts/ and run:
    python scripts/ingest_bare_acts.py

Supported file naming convention:
    BNS.txt   → Bharatiya Nyaya Sanhita, 2023   (regime: bns_bnss)
    BNSS.txt  → Bharatiya Nagarik Suraksha Sanhita, 2023 (regime: bns_bnss)
    BSA.txt   → Bharatiya Sakshya Adhiniyam, 2023 (regime: bns_bnss)
    IPC.txt   → Indian Penal Code, 1860          (regime: ipc_crpc)
    CrPC.txt  → Code of Criminal Procedure, 1973 (regime: ipc_crpc)

Section parsing heuristics (handles most bare-act formatting):
    "Section 1." / "1." / "1. Short title." / "SECTION 1" etc.

Output:
    data/chroma_db/   — ChromaDB persistent vector store
    data/chroma_db/bm25_index.pkl — Serialised BM25 index
"""

from __future__ import annotations

import os
import pickle
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

# Make project root importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import config AFTER sys.path fix
from src.config import (
    PROJECT_ROOT as CFG_ROOT,
    RAG_COLLECTION_NAME,
    RAG_EMBED_MODEL,
    RAG_PERSIST_DIR,
    RAG_SOURCE_DIR,
)

# ---------------------------------------------------------------------------
# Act metadata registry
# ---------------------------------------------------------------------------

ACT_REGISTRY: dict[str, dict[str, str]] = {
    "BNS": {
        "full_name": "Bharatiya Nyaya Sanhita, 2023",
        "regime": "bns_bnss",
    },
    "BNSS": {
        "full_name": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "regime": "bns_bnss",
    },
    "BSA": {
        "full_name": "Bharatiya Sakshya Adhiniyam, 2023",
        "regime": "bns_bnss",
    },
    "IPC": {
        "full_name": "Indian Penal Code, 1860",
        "regime": "ipc_crpc",
    },
    "CRPC": {
        "full_name": "Code of Criminal Procedure, 1973",
        "regime": "ipc_crpc",
    },
    "CrPC": {
        "full_name": "Code of Criminal Procedure, 1973",
        "regime": "ipc_crpc",
    },
}

# ---------------------------------------------------------------------------
# Text pre-cleaner
# ---------------------------------------------------------------------------

# Page numbers: standalone digits on a line, optionally prefixed by page/pg/p.
_PAGE_NUMBER_RE = re.compile(
    r'^[ \t]*(?:Page|Pg\.?|P\.)?[ \t]*\d{1,4}[ \t]*$',
    re.MULTILINE | re.IGNORECASE,
)

# Running headers / footers: short ALL-CAPS lines that repeat verbatim
# (detected dynamically in clean_text below)
_SHORT_ALLCAPS_RE = re.compile(r'^[A-Z ,&.()\d]{5,80}$')

# Form-feed characters inserted by pdftotext between pages
_FORM_FEED_RE = re.compile(r'\f')

# Multiple blank lines → two newlines max
_MULTI_BLANK_RE = re.compile(r'\n{3,}')


def clean_text(text: str) -> str:
    """Pre-process raw pdftotext output to remove noise.

    Steps:
      1. Replace form-feeds (page breaks) with a blank line.
      2. Strip standalone page-number lines.
      3. Remove repeated short ALL-CAPS header/footer lines
         (appears >= 3 times → likely a running header).
      4. Collapse runs of 3+ blank lines into two.
      5. Strip leading/trailing whitespace per line.
    """
    # 1. Form feeds → blank line
    text = _FORM_FEED_RE.sub('\n\n', text)

    # 2. Page numbers
    text = _PAGE_NUMBER_RE.sub('', text)

    # 3. Detect and remove repeated short ALL-CAPS lines (running headers/footers)
    line_counts: dict[str, int] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and _SHORT_ALLCAPS_RE.match(stripped):
            line_counts[stripped] = line_counts.get(stripped, 0) + 1
    # Any line that appears >= 3 times is treated as a running header/footer
    repeated_headers = {ln for ln, cnt in line_counts.items() if cnt >= 3}
    if repeated_headers:
        cleaned_lines = []
        for line in text.splitlines():
            if line.strip() in repeated_headers:
                continue
            cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)

    # 4. Collapse excess blank lines
    text = _MULTI_BLANK_RE.sub('\n\n', text)

    # 5. Strip trailing whitespace per line (keeps leading indent intact)
    text = '\n'.join(ln.rstrip() for ln in text.splitlines())

    return text.strip()


# ---------------------------------------------------------------------------
# Section header recogniser — handles all real pdftotext variants
# ---------------------------------------------------------------------------

# Each pattern group captures:
#   group 1 — section number (digits, optional letter suffix e.g. 100A)
#   group 2 — section title / inline text (may be empty)
#
# Variants handled:
#   "Section 1."          "Section 1 Short title"   "Section 1—Short title"
#   "SECTION 318."        "Sec. 100."               "Sec 100"
#   "1."  "1. Short"      "1  Short title"           (bare number with title)
#   Sub-sections like 318(1) are detected and tagged but NOT treated as
#   new top-level sections — they are merged into their parent.

# Primary: explicit "Section" / "SECTION" / "Sec." keyword (high confidence)
_HDR_KEYWORD = re.compile(
    r'''
    ^[ \t]*                     # optional leading whitespace
    (?:Section|SECTION|Sec\.)   # keyword
    [ \t]+
    (\d{1,3}[A-Z]?)             # section number
    (?:[ \t]*[.\-\u2014\u2013:])? # optional separator
    [ \t]*
    ([^\n]{0,150})              # optional title on same line
    ''',
    re.VERBOSE | re.MULTILINE,
)

# Secondary: bare number at start of line, MUST have a separator or CAPS title
# to avoid matching sub-section prose like "(1) The provisions..."
_HDR_BARE = re.compile(
    r'''
    ^[ \t]*
    (\d{1,3}[A-Z]?)             # section number (max 3 digits to avoid year matches)
    [ \t]*
    (?:
        [.\-\u2014\u2013]        # separator char
        [ \t]*([^\n]{0,150})    # title
        |
        [ \t]+([A-Z][^\n]{2,150}) # OR a CAPS-starting title directly after space
    )
    ''',
    re.VERBOSE | re.MULTILINE,
)

# Sub-section marker: 318(1), 318(2)(a) — used to detect but NOT split
_SUB_SECTION_RE = re.compile(r'^\d{1,3}[A-Z]?\(\d+\)', re.MULTILINE)


def _find_section_headers(text: str) -> list[tuple[int, str, str]]:
    """Find all section header positions in text.

    Returns a list of (start_pos, section_number, section_title) tuples
    in document order. Sub-sections (e.g. 318(1)) are excluded.
    """
    hits: dict[int, tuple[str, str]] = {}  # pos → (num, title)

    # Pass 1 — keyword-anchored headers (high confidence, processed first)
    for m in _HDR_KEYWORD.finditer(text):
        num   = m.group(1).strip()
        title = (m.group(2) or '').strip().strip('.\u2014\u2013\u2012-:')
        hits[m.start()] = (num, title)

    # Pass 2 — bare-number headers (lower confidence, only add if not already covered)
    for m in _HDR_BARE.finditer(text):
        pos = m.start()
        # Skip if a keyword-match already covers this position (±5 chars)
        if any(abs(pos - k) < 5 for k in hits):
            continue
        num   = m.group(1).strip()
        title = ((m.group(2) or '') + (m.group(3) or '')).strip().strip('.\u2014\u2013-:')

        # Guard: skip if looks like a sub-section reference (e.g. "318(1)")
        # by checking the character immediately following the number
        after_num = text[m.start() + len(num) : m.start() + len(num) + 1]
        if after_num == '(':
            continue

        hits[pos] = (num, title)

    # Sort by position
    return sorted((pos, num, title) for pos, (num, title) in hits.items())


def _promote_next_line_title(body: str, existing_title: str) -> tuple[str, str]:
    """If the section header line had no title, try to pull the title
    from the first non-blank line of the body text.

    This handles the pattern:
        Section 85.
        Husband or relative of husband of a woman subjecting her to cruelty.
        Whoever, being...

    Returns (promoted_title, remaining_body).
    """
    if existing_title:
        return existing_title, body

    lines = body.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # A title candidate: short, doesn't start with a bracket, not all digits
        if (
            len(stripped) <= 140
            and not stripped.startswith('(')
            and not stripped[0].isdigit()
            and stripped.endswith('.')
            and '\n' not in stripped
        ):
            remaining = '\n'.join(lines[i + 1 :]).strip()
            return stripped.rstrip('.'), remaining
        break  # First non-blank line was not title-like; stop

    return existing_title, body


# ---------------------------------------------------------------------------
# Main section splitter (public API — called from main())
# ---------------------------------------------------------------------------

def split_into_sections(text: str, act: str, source_file: str) -> list[dict[str, Any]]:
    """Parse a raw bare-act text file into per-section documents.

    Pipeline:
      1. clean_text  — remove page numbers, headers, OCR noise
      2. _find_section_headers  — multi-pattern header detection
      3. _promote_next_line_title  — recover titles on next line
      4. Merge sub-sections into parent (318(1) → 318)
      5. Emit one document per top-level section

    Each returned dict has:
        id, document, act, section_number, section_title, regime, source_file
    """
    info   = ACT_REGISTRY.get(act.upper(), ACT_REGISTRY.get(act, {}))
    regime = info.get('regime', 'unknown')

    # --- Step 1: Clean ---
    text = clean_text(text)

    # --- Step 2: Find headers ---
    headers = _find_section_headers(text)

    if not headers:
        # Fallback: treat whole file as one chunk
        return [{
            'id':           f'{act}_FULL_{uuid.uuid4().hex[:8]}',
            'document':     text.strip(),
            'act':          act,
            'section_number': 'FULL',
            'section_title':  info.get('full_name', act),
            'regime':       regime,
            'source_file':  source_file,
        }]

    sections = []
    seen_ids: dict[str, int] = {}  # track duplicates

    for i, (pos, sec_num, sec_title) in enumerate(headers):
        # Body = text from end of header line to start of next header
        header_end = text.index('\n', pos) + 1 if '\n' in text[pos:] else len(text)
        body_end   = headers[i + 1][0] if i + 1 < len(headers) else len(text)
        body       = text[header_end:body_end].strip()

        if not body:
            continue

        # --- Step 3: Promote next-line title ---
        sec_title, body = _promote_next_line_title(body, sec_title)

        # --- Step 4: Merge sub-sections --- already inside body naturally;
        # no split needed — body includes all sub-section text.
        # Tag sub-section count for transparency.
        sub_count = len(_SUB_SECTION_RE.findall(body))

        # --- Step 5: Build output dict ---
        clean_title = sec_title.strip('\u2014\u2013.\u2012 -:').strip()

        if clean_title:
            header_line = f'Section {sec_num}. {clean_title}'
        else:
            header_line = f'Section {sec_num}.'

        full_document = f'{header_line}\n\n{body}'

        # De-duplicate IDs (same section number appearing twice in file)
        raw_id = f'{act}_{sec_num}'
        if raw_id in seen_ids:
            seen_ids[raw_id] += 1
            doc_id = f'{raw_id}_dup{seen_ids[raw_id]}'
        else:
            seen_ids[raw_id] = 0
            doc_id = raw_id

        sections.append({
            'id':             doc_id,
            'document':       full_document,
            'act':            act,
            'section_number': sec_num,
            'section_title':  clean_title,
            'regime':         regime,
            'source_file':    source_file,
        })

    print(
        f'  [{act}] Parsed {len(sections)} top-level sections '
        f'from {source_file} '
        f'(headers found: {len(headers)})'
    )
    return sections


# ---------------------------------------------------------------------------
# ChromaDB + BM25 indexer
# ---------------------------------------------------------------------------

def index_sections(all_sections: list[dict[str, Any]]) -> None:
    """Embed and upsert sections into ChromaDB; build BM25 index."""

    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError:
        print("ERROR: chromadb and sentence-transformers are required.")
        print("Run: pip install chromadb sentence-transformers rank-bm25")
        sys.exit(1)

    persist_path = str(PROJECT_ROOT / RAG_PERSIST_DIR)
    Path(persist_path).mkdir(parents=True, exist_ok=True)

    print(f"\nConnecting to ChromaDB at: {persist_path}")
    client = chromadb.PersistentClient(path=persist_path)

    embed_fn = SentenceTransformerEmbeddingFunction(
        model_name=RAG_EMBED_MODEL,
        device="cpu",
    )

    # Delete existing collection to allow clean re-index
    try:
        client.delete_collection(name=RAG_COLLECTION_NAME)
        print(f"Dropped existing collection '{RAG_COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=RAG_COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # Batch upsert (ChromaDB recommends batches of ~1000)
    BATCH_SIZE = 500
    total = len(all_sections)
    print(f"\nIndexing {total} sections into ChromaDB (batch size={BATCH_SIZE}) …")

    for start in range(0, total, BATCH_SIZE):
        batch = all_sections[start : start + BATCH_SIZE]
        collection.add(
            ids=[s["id"] for s in batch],
            documents=[s["document"] for s in batch],
            metadatas=[
                {
                    "act": s["act"],
                    "section_number": s["section_number"],
                    "section_title": s["section_title"],
                    "regime": s["regime"],
                    "source_file": s["source_file"],
                }
                for s in batch
            ],
        )
        end = min(start + BATCH_SIZE, total)
        print(f"  Upserted sections {start + 1}–{end} / {total}")

    print(f"ChromaDB indexing complete. Collection has {collection.count()} docs.")

    # Build BM25 index
    _build_bm25(all_sections, persist_path)


def _build_bm25(sections: list[dict[str, Any]], persist_path: str) -> None:
    """Build and serialise a BM25Okapi index for sparse retrieval."""
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        print("WARNING: rank-bm25 not installed. Skipping BM25 index.")
        print("Run: pip install rank-bm25")
        return

    print("\nBuilding BM25 index …")
    corpus = [s["document"].lower().split() for s in sections]
    ids = [s["id"] for s in sections]

    bm25 = BM25Okapi(corpus)
    bm25_path = Path(persist_path) / "bm25_index.pkl"
    with open(bm25_path, "wb") as fh:
        pickle.dump({"bm25": bm25, "ids": ids}, fh)

    print(f"BM25 index saved to: {bm25_path} ({len(ids)} docs)")


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    source_dir = PROJECT_ROOT / RAG_SOURCE_DIR
    if not source_dir.exists():
        print(f"ERROR: Source directory does not exist: {source_dir}")
        print(f"Create it and place your bare-act .txt files inside.")
        sys.exit(1)

    txt_files = sorted(source_dir.glob("*.txt"))
    if not txt_files:
        print(f"No .txt files found in {source_dir}")
        print("Expected files: BNS.txt, BNSS.txt, BSA.txt, IPC.txt, CrPC.txt")
        sys.exit(1)

    print(f"Found {len(txt_files)} source file(s):")
    for f in txt_files:
        print(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    all_sections: list[dict[str, Any]] = []
    t0 = time.perf_counter()

    for txt_file in txt_files:
        act_key = txt_file.stem.upper()
        # Normalize "CRPC" → "CrPC" for display
        if act_key not in ACT_REGISTRY:
            print(f"  WARNING: '{txt_file.name}' not in ACT_REGISTRY, skipping.")
            continue

        print(f"\nParsing {txt_file.name} …")
        text = txt_file.read_text(encoding="utf-8", errors="replace")
        sections = split_into_sections(text, act_key, txt_file.name)
        all_sections.extend(sections)

    if not all_sections:
        print("ERROR: No sections were parsed. Check your file formats.")
        sys.exit(1)

    print(f"\nTotal sections parsed: {len(all_sections)}")
    index_sections(all_sections)

    elapsed = time.perf_counter() - t0
    print(f"\n✅ Ingestion complete in {elapsed:.1f}s")
    print(f"   Run your NyayaPath server — local RAG is now the primary retrieval path.")


if __name__ == "__main__":
    main()
