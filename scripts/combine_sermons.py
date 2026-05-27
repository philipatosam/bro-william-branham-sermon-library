#!/usr/bin/env python3
"""
Combine individual sermon JSON files into one master JSON.

Usage:
    python3 scripts/combine_sermons.py --input output --output combined/branham_sermons.json
"""

import json
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)-8s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def main():
    ap = argparse.ArgumentParser(
        description="Combine individual sermon JSONs into one master file")
    ap.add_argument("--input",  "-i", required=True,
                    help="Folder containing individual sermon JSON files")
    ap.add_argument("--output", "-o", required=True,
                    help="Output path for combined JSON file")
    args = ap.parse_args()

    input_dir  = Path(args.input).expanduser()
    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_dir.is_dir():
        log.error("Input folder not found: %s", input_dir)
        raise SystemExit(1)

    # Collect and sort all JSON files by sermon ID (filename order = date order)
    json_files = sorted(input_dir.glob("*.json"))
    log.info("Found %d sermon JSON files in %s", len(json_files), input_dir)

    sermons = []
    failed  = []

    for i, json_file in enumerate(json_files, 1):
        try:
            with open(json_file, encoding="utf-8") as f:
                sermon = json.load(f)
            sermons.append(sermon)
            log.info("[%d/%d] ✓ %s", i, len(json_files), json_file.name)
        except Exception as exc:
            log.error("[%d/%d] FAILED %s — %s", i, len(json_files), json_file.name, exc)
            failed.append(json_file.name)

    log.info("=" * 60)
    log.info("Loaded: %d sermons  |  %d failed", len(sermons), len(failed))
    if failed:
        log.warning("Failed files: %s", ", ".join(failed))

    # Build master JSON
    master = {
        "name":        "William Marrion Branham Sermons",
        "description": f"Complete sermon library — {len(sermons)} messages by William Marrion Branham.",
        "total":       len(sermons),
        "sermons":     sermons,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(master, f, ensure_ascii=False, indent=2)

    size_mb = output_path.stat().st_size / 1_048_576
    log.info("Written to: %s  (%.1f MB)", output_path, size_mb)


if __name__ == "__main__":
    main()
