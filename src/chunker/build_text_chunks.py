import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


PROJECT_ROOT = Path("/root/autodl-tmp/kd_agent_pipeline")

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "parsed_pages.jsonl"
CHUNK_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "text_chunks.jsonl"
OCR_TODO_PATH = PROJECT_ROOT / "data" / "processed" / "ocr_todo_pages.jsonl"

MAX_CHARS = 1200
MIN_CHARS = 120
OVERLAP_CHARS = 150


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_paragraphs(text: str) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)
    cleaned = []

    for p in paragraphs:
        p = p.strip()
        if p:
            cleaned.append(p)

    return cleaned


def build_chunks_for_page(page_record: Dict) -> List[Dict]:
    text = normalize_text(page_record.get("text", ""))

    if not text:
        return []

    paragraphs = split_paragraphs(text)

    chunks = []
    buffer = ""

    for para in paragraphs:
        if not buffer:
            buffer = para
            continue

        if len(buffer) + len(para) + 2 <= MAX_CHARS:
            buffer = buffer + "\n\n" + para
        else:
            if len(buffer) >= MIN_CHARS:
                chunks.append(buffer)

            if len(buffer) > OVERLAP_CHARS:
                overlap = buffer[-OVERLAP_CHARS:]
                buffer = overlap + "\n\n" + para
            else:
                buffer = para

    if buffer and len(buffer) >= MIN_CHARS:
        chunks.append(buffer)

    output = []

    for idx, chunk_text in enumerate(chunks):
        chunk_id = (
            f"{page_record['discipline']}_"
            f"{page_record['source_file'].replace('.', '_')}_"
            f"p{page_record['page']}_"
            f"c{idx}"
        )

        output.append({
            "chunk_id": chunk_id,
            "source_file": page_record["source_file"],
            "source_path": page_record["source_path"],
            "discipline": page_record["discipline"],
            "page": page_record["page"],
            "content_type": "pdf_text_chunk",
            "parse_method": page_record.get("parse_method", "pymupdf_text"),
            "needs_ocr": bool(page_record.get("needs_ocr", False)),
            "is_scanned_or_image_page": bool(page_record.get("is_scanned_or_image_page", False)),
            "citation_anchor": page_record["citation_anchor"],
            "text": chunk_text,
            "text_length": len(chunk_text),
            "chunk_index_in_page": idx,
        })

    return output


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Please run src/parser/parse_pdf_pages.py first."
        )

    CHUNK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    total_pages = 0
    text_pages = 0
    ocr_pages = 0
    total_chunks = 0

    with CHUNK_OUTPUT_PATH.open("w", encoding="utf-8") as chunk_out, \
         OCR_TODO_PATH.open("w", encoding="utf-8") as ocr_out:

        for page_record in load_jsonl(INPUT_PATH):
            total_pages += 1

            if page_record.get("needs_ocr"):
                ocr_pages += 1
                ocr_out.write(json.dumps({
                    "source_file": page_record["source_file"],
                    "source_path": page_record["source_path"],
                    "discipline": page_record["discipline"],
                    "page": page_record["page"],
                    "content_type": "ocr_todo_page",
                    "needs_ocr": True,
                    "citation_anchor": page_record["citation_anchor"],
                    "ocr_status": "pending",
                    "text_length": page_record.get("text_length", 0),
                }, ensure_ascii=False) + "\n")
                continue

            text_pages += 1
            chunks = build_chunks_for_page(page_record)

            for chunk in chunks:
                chunk_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                total_chunks += 1

    print("Text chunking finished.")
    print(f"Input pages: {total_pages}")
    print(f"Text pages: {text_pages}")
    print(f"OCR todo pages: {ocr_pages}")
    print(f"Generated chunks: {total_chunks}")
    print(f"Chunk output: {CHUNK_OUTPUT_PATH}")
    print(f"OCR todo output: {OCR_TODO_PATH}")


if __name__ == "__main__":
    main()
