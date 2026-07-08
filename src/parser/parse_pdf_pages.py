import json
from pathlib import Path
import os
from typing import Dict, List

import fitz  # PyMuPDF


PROJECT_ROOT = Path(os.environ.get("KD_AGENT_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "parsed_pages.jsonl"

MIN_TEXT_CHARS = 50


def parse_pdf(pdf_path: Path) -> List[Dict]:
    records = []

    doc = fitz.open(pdf_path)

    for page_index, page in enumerate(doc):
        text = page.get_text("text") or ""
        text = text.strip()

        is_scanned = len(text) < MIN_TEXT_CHARS

        record = {
            "source_file": pdf_path.name,
            "source_path": str(pdf_path),
            "discipline": pdf_path.parent.name,
            "page": page_index,
            "content_type": "pdf_page",
            "parse_method": "pymupdf_text",
            "text": text,
            "text_length": len(text),
            "is_scanned_or_image_page": is_scanned,
            "needs_ocr": is_scanned,
            "citation_anchor": f"{pdf_path.name}#page={page_index}",
        }

        records.append(record)

    return records


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(RAW_DIR.rglob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {RAW_DIR}")
        return

    total_pages = 0
    scanned_pages = 0

    with OUTPUT_PATH.open("w", encoding="utf-8") as out:
        for pdf_path in pdf_files:
            print(f"Parsing PDF: {pdf_path}")
            records = parse_pdf(pdf_path)

            for record in records:
                out.write(json.dumps(record, ensure_ascii=False) + "\n")

            total_pages += len(records)
            scanned_pages += sum(1 for r in records if r["needs_ocr"])

    print("PDF parsing finished.")
    print(f"PDF files: {len(pdf_files)}")
    print(f"Total pages: {total_pages}")
    print(f"Pages requiring OCR: {scanned_pages}")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
