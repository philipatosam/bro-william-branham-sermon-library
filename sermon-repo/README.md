# 📖 Bro. William Marrion Branham — Sermon Library (JSON)

A freely available, machine-readable JSON library of **1,206 sermons** by Brother William Marrion Branham, converted from the official VGR PDF editions. This project exists to promote the further spreading of the Gospel and to make Brother Branham's messages more accessible to developers, researchers, and ministry tools worldwide.

---

## 🙏 Credits & Acknowledgements

- **[Voice of God Recordings (VGR)](https://www.branham.org)** — the official custodians of Brother Branham's sermons. All content originates from their meticulously preserved PDF editions. VGR states that their materials may be freely distributed for the purpose of spreading the Gospel, which is the sole intent of this project.

- **[branham-player/golden-dataset](https://github.com/branham-player/golden-dataset)** — the open-source metadata repository that provided sermon titles, dates, locations, and building information used to enrich every JSON file in this library. This project would not have the same quality without their work.

---

## 📦 What's in This Repo

```
bro-william-branham-sermon-library/
├── output/                         # 1,206 individual sermon JSON files
│   ├── 47-0412 Faith Is the Substance.json
│   ├── 47-0414 Death.json
│   └── ... (one file per sermon)
├── scripts/
│   ├── convert_sermons.py          # PDF → individual JSON converter
│   └── combine_sermons.py          # Merge individual JSONs → one master file
├── metadata/
│   └── full.json                   # Sermon metadata from branham-player/golden-dataset
├── .gitignore
├── LICENSE
└── README.md
```

> **Combined file:** The single master `branham_sermons.json` (~150–200 MB) is too large for GitHub. Download it from the [**Releases**](https://github.com/philipatosam/bro-william-branham-sermon-library/releases) page.

---

## 📄 JSON Structure

### Individual sermon file (`output/47-0412 Faith Is the Substance.json`)

```json
{
  "id": "47-0412",
  "title": "Faith Is the Substance",
  "meta": {
    "date": "April 12th, 1947",
    "location": "Oakland, California",
    "building": "Oakland Municipal Auditorium",
    "building_known": true
  },
  "paragraphs": [
    {
      "number": 1,
      "text": "We're getting some new gadgets for recording."
    },
    {
      "number": 2,
      "text": "We hardly know each night where we're going to be at..."
    }
  ]
}
```

### Combined master file (`branham_sermons.json`)

```json
{
  "name": "William Marrion Branham Sermons",
  "description": "Complete sermon library — 1,206 messages by William Marrion Branham.",
  "total": 1206,
  "sermons": [
    { "id": "47-0412", "title": "...", "meta": {...}, "paragraphs": [...] },
    { "id": "47-0414", ... },
    ...
  ]
}
```

---

## 🚀 Using the Scripts

### Requirements

```bash
pip install pymupdf
```

### Convert PDFs to individual JSONs

```bash
python3 scripts/convert_sermons.py \
  --input /path/to/pdfs \
  --output output
```

### Combine individual JSONs into one master file

```bash
python3 scripts/combine_sermons.py \
  --input output \
  --output combined/branham_sermons.json
```

### Options

| Flag | Description |
|---|---|
| `--input` | Input folder (PDFs or JSONs) |
| `--output` | Output folder or file path |
| `--metadata` | Path to local `full.json` metadata (skips GitHub fetch) |
| `--limit N` | Process only first N files (useful for testing) |

---

## 📋 Sermon Coverage

- **Total sermons:** 1,206
- **Date range:** 1947 – 1965
- **Languages:** English
- **Source format:** VGR PDF editions
- **Paragraphs:** Each sermon paragraph is individually numbered, matching the original VGR paragraph numbering

---

## ⚠️ Notes on Parsing

- Paragraphs are extracted using [PyMuPDF](https://pymupdf.readthedocs.io/) in block mode, which preserves correct word spacing from the original PDFs
- The VGR eagle symbol (``) marks the start and end of each sermon's content
- **29 sermons** have unknown building information — these are mostly from the 1955 Europe tour (Zurich, Karlsruhe, Lausanne) and a few early US meetings
- If you find a parsing error in any sermon, please open an issue with the sermon ID

---

## 🤝 Contributing

Pull requests are welcome. If you notice a parsing error, incorrect metadata, or a missing sermon, please:

1. Open an issue with the sermon ID and description of the problem
2. Or submit a PR with the corrected JSON file directly

---

## 📜 License

**Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

You are free to share and adapt this data for any **non-commercial** purpose, provided you give appropriate credit to:
- Voice of God Recordings (VGR) — original sermon content
- [branham-player/golden-dataset](https://github.com/branham-player/golden-dataset) — sermon metadata
- This repository — conversion and structuring

Commercial use is not permitted. This project exists solely to promote the Gospel of Jesus Christ.

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

---

## 🔗 Related

- [Voice of God Recordings](https://www.branham.org) — official VGR website
- [branham.org sermons](https://branham.org/en/sermons) — official online sermon library
- [branham-player/golden-dataset](https://github.com/branham-player/golden-dataset) — metadata source

---

*"Go ye into all the world and preach the Gospel to every creature." — Mark 16:15*
