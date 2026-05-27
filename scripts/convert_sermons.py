#!/usr/bin/env python3
"""
VGR Sermon PDF → Individual JSON files
Outputs one JSON file per sermon into the output folder.

Usage:
    python3 scripts/convert_sermons.py --input pdfs --output output
    python3 scripts/convert_sermons.py --input pdfs --output output --limit 5
    python3 scripts/convert_sermons.py --input pdfs --output output --metadata metadata/full.json
"""

import re
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Optional

try:
    import fitz  # pymupdf
except ImportError:
    print("ERROR: pymupdf not installed. Run: pip install pymupdf")
    sys.exit(1)

EAGLE_CHAR  = "\uf6e1"
SPOKEN_WORD = "THE SPOKEN WORD"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)-8s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


# ── Text cleanup ───────────────────────────────────────────────────────────────
def clean(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


# ── Detect how many trailing pages to skip ────────────────────────────────────
def pages_to_skip(doc) -> int:
    """
    Detect whether this PDF has a location/building info page before copyright.

    Every PDF always ends with:
      - Last page:           Copyright Notice  (always skip)
      - Second-to-last page: Location page     (skip IF it exists)
                             OR content page   (don't skip if no location page)

    Detection: the location page always contains the VGR sermon date code
    e.g. '47-0412 Faith Is The Substance' — a reliable unique marker.
    If found on the penultimate page → skip 2.
    If not found → skip only 1 (copyright only).
    """
    total = doc.page_count
    if total < 2:
        return 0

    penultimate_text = ""
    for block in doc[total - 2].get_text("blocks"):
        penultimate_text += block[4]

    # VGR location page always starts with the sermon date code: 'YY-MMDD'
    has_location_page = bool(re.search(r"\d{2}-\d{4}", penultimate_text))

    return 2 if has_location_page else 1


# ── Page header detection ──────────────────────────────────────────────────────
def is_header_block(raw: str) -> bool:
    """
    Detect running page-header blocks — never sermon content.
    Even pages:  '2\nTHE SPOKEN WORD\n'
    Odd pages:   'FAITH IS THE SUBSTANCE\n3\n'
    """
    if SPOKEN_WORD in raw:
        return True
    t = raw.strip()
    if len(t) < 80:
        core = re.sub(r"\n?\d+\s*$", "", t).strip()
        if core and re.match(r"^[A-Z][A-Z\s'\.,\-–—]+$", core):
            return True
    return False


# ── Block helpers ──────────────────────────────────────────────────────────────
def parse_block(text: str) -> tuple:
    """Return (paragraph_number, body) or (None, text) if no leading number."""
    m = re.match(r"^(\d{1,4})\s+(.*)", text, re.DOTALL)
    if m:
        return int(m.group(1)), clean(m.group(2))
    return None, text


def _is_next(paragraphs: list, num: int) -> bool:
    """True if num is the plausible next sequential paragraph number."""
    if not paragraphs:
        return num == 2
    last = paragraphs[-1]["number"]
    return last < num <= last + 10


# ── Core extractor ─────────────────────────────────────────────────────────────
def extract_paragraphs(pdf_path: str) -> list:
    """
    Extract all paragraphs from a VGR sermon PDF using pymupdf block mode.

    Dynamically detects how many trailing pages to skip:
      - Always skips the copyright page (last page)
      - Also skips the location/building page (second-to-last) if present
    """
    paragraphs   = []
    found_eagle  = False
    done         = False

    pending_num  = None
    pending_text = ""

    def flush_pending():
        nonlocal pending_num, pending_text
        if pending_num is not None and pending_text.strip():
            paragraphs.append({"number": pending_num, "text": pending_text.strip()})
        pending_num  = None
        pending_text = ""

    doc    = fitz.open(pdf_path)
    total  = doc.page_count
    skip   = pages_to_skip(doc)
    limit  = total - skip

    log.debug("  %d pages total, skipping last %d", total, skip)

    for pg_idx in range(limit):
        if done:
            break

        for block in doc[pg_idx].get_text("blocks"):
            if done:
                break

            raw  = block[4]

            if is_header_block(raw):
                continue

            text = clean(raw)
            if not text:
                continue

            # ── Eagle handling ─────────────────────────────────────────────
            if EAGLE_CHAR in text:
                before, _, after = text.partition(EAGLE_CHAR)
                before = before.strip()
                after  = after.strip()

                if not found_eagle:
                    # First eagle: everything after = paragraph 1
                    found_eagle = True
                    if after:
                        paragraphs.append({"number": 1, "text": after})

                else:
                    # Second eagle: close last paragraph
                    if before:
                        num, body = parse_block(before)
                        if num is not None and _is_next(paragraphs, num):
                            flush_pending()
                            if body:
                                paragraphs.append({"number": num, "text": body})
                        else:
                            pending_text = (pending_text + " " + before).strip()
                            flush_pending()
                    else:
                        flush_pending()
                    done = True
                continue

            if not found_eagle:
                continue

            # ── Numbered paragraph block ───────────────────────────────────
            num, body = parse_block(text)

            if num is not None and _is_next(paragraphs, num):
                flush_pending()
                pending_num  = num
                pending_text = body
            else:
                # Continuation block
                if pending_num is not None:
                    pending_text = (pending_text + " " + text).strip()
                elif paragraphs:
                    paragraphs[-1]["text"] = (
                        paragraphs[-1]["text"] + " " + text
                    ).strip()

    # Safety flush — catches sermons where second eagle is missing
    flush_pending()

    doc.close()
    return paragraphs


# ── Metadata ───────────────────────────────────────────────────────────────────
def load_metadata(metadata_path: Optional[str]) -> dict:
    meta = {}

    def _parse(raw):
        for item in raw:
            sid = item.get("id", "")
            if sid:
                meta[sid] = item
        return meta

    if metadata_path and Path(metadata_path).exists():
        log.info("Loading metadata from %s", metadata_path)
        with open(metadata_path, encoding="utf-8") as f:
            return _parse(json.load(f))

    try:
        import urllib.request
        url = ("https://raw.githubusercontent.com/branham-player/"
               "golden-dataset/refs/heads/master/deploy/full.json")
        log.info("Fetching metadata from GitHub...")
        with urllib.request.urlopen(url, timeout=30) as resp:
            return _parse(json.loads(resp.read()))
    except Exception as exc:
        log.warning("Could not fetch metadata (%s). Using filename fallback.", exc)

    return meta


def resolve_title(sermon_id: str, metadata: dict) -> str:
    if sermon_id in metadata:
        return metadata[sermon_id]["title"]["displayName"]
    name = re.sub(r"^\d{2}-\d{4}[A-Z]?_?", "", sermon_id)
    name = re.sub(r"_VGR$", "", name)
    return name.replace("_", " ").title()


def resolve_meta(sermon_id: str, metadata: dict) -> dict:
    if sermon_id not in metadata:
        return {}
    m = metadata[sermon_id]
    return {
        "date":         m.get("date",     {}).get("displayName", ""),
        "location":     m.get("location", {}).get("displayName", ""),
        "building":     m.get("building", {}).get("displayName", ""),
        "building_known": m.get("building", {}).get("known", False),
    }


# ── Safe filename helper ───────────────────────────────────────────────────────
def safe_filename(sermon_id: str, title: str) -> str:
    """Build '{sermon_id} {title}.json', stripping invalid filename chars."""
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    return f"{sermon_id} {safe_title}.json"


# ── Single PDF processor ───────────────────────────────────────────────────────
def process_pdf(pdf_path: Path, output_dir: Path, metadata: dict) -> bool:
    filename  = pdf_path.stem
    m         = re.match(r"^(\d{2}-\d{4}[A-Z]?)", filename)
    sermon_id = m.group(1) if m else filename

    title    = resolve_title(sermon_id, metadata)
    meta     = resolve_meta(sermon_id, metadata)
    out_name = safe_filename(sermon_id, title)
    out_file = output_dir / out_name

    if out_file.exists():
        log.info("SKIP (exists): %s", out_name)
        return True

    log.info("Processing: %-12s  %s", sermon_id, title)

    try:
        paragraphs = extract_paragraphs(str(pdf_path))
    except Exception as exc:
        log.error("  FAILED %s — %s", pdf_path.name, exc)
        return False

    if not paragraphs:
        log.warning("  WARNING: No paragraphs found in %s", pdf_path.name)
        return False

    sermon = {
        "id":         sermon_id,
        "title":      title,
        "meta":       meta,
        "paragraphs": paragraphs,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(sermon, f, ensure_ascii=False, indent=2)

    log.info("  ✓ %d paragraphs → %s", len(paragraphs), out_name)
    return True


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="Convert VGR Sermon PDFs to individual JSON files")
    ap.add_argument("--input",    "-i", required=True,
                    help="Folder containing PDF sermons")
    ap.add_argument("--output",   "-o", required=True,
                    help="Output folder for individual JSON files")
    ap.add_argument("--metadata", "-m", default=None,
                    help="Path to local full.json metadata file (optional)")
    ap.add_argument("--limit",    type=int, default=None,
                    help="Process only first N PDFs (for testing)")
    args = ap.parse_args()

    metadata   = load_metadata(args.metadata)
    log.info("Metadata: %d entries loaded", len(metadata))

    input_path = Path(args.input).expanduser()
    output_dir = Path(args.output).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.is_dir():
        log.error("Input folder not found: %s", input_path)
        sys.exit(1)

    pdf_files = sorted(input_path.glob("*.pdf"))
    log.info("Found %d PDFs in %s", len(pdf_files), input_path)

    if args.limit:
        pdf_files = pdf_files[: args.limit]
        log.info("Limiting to first %d PDFs", args.limit)

    success, failed = 0, []
    for i, pdf_path in enumerate(pdf_files, 1):
        log.info("[%d/%d]", i, len(pdf_files))
        ok = process_pdf(pdf_path, output_dir, metadata)
        if ok:
            success += 1
        else:
            failed.append(pdf_path.name)

    log.info("=" * 60)
    log.info("Done: %d succeeded  |  %d failed", success, len(failed))
    log.info("JSON files written to: %s", output_dir)
    if failed:
        log.warning("Failed files:")
        for f in failed:
            log.warning("  %s", f)


if __name__ == "__main__":
    main()
