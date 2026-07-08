import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import sys
from typing import Dict, List, Tuple


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.paths import PROJECT_ROOT

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "parsed_pages.jsonl"
CHUNK_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "text_chunks.jsonl"
OCR_TODO_PATH = PROJECT_ROOT / "data" / "processed" / "ocr_todo_pages.jsonl"
OCR_CACHE_PATHS = [
    PROJECT_ROOT / "data" / "processed" / "ocr_pages.jsonl",
    PROJECT_ROOT / "data" / "processed" / "cs_cn_ocr_selected_pages.jsonl",
]
OCR_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "ocr_pages.jsonl"

ENABLE_OCR = os.getenv("ENABLE_OCR", "1") == "1"
OCR_LANG = os.getenv("OCR_LANG", "chi_sim+eng")
OCR_MAX_PAGES = int(os.getenv("OCR_MAX_PAGES", "0"))
OCR_RENDER_SCALE = float(os.getenv("OCR_RENDER_SCALE", "1.8"))

MAX_CHARS = 1200
MIN_CHARS = 120
OVERLAP_CHARS = 150


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def load_ocr_cache(paths: List[Path]) -> Dict[Tuple[str, int], str]:
    cache: Dict[Tuple[str, int], str] = {}

    for path in paths:
        if not path.exists():
            continue

        for item in load_jsonl(path):
            source_file = item.get("source_file")
            text = (item.get("text") or "").strip()
            if not source_file or not text:
                continue

            try:
                page = int(item.get("page"))
            except (TypeError, ValueError):
                continue

            cache[(source_file, page)] = text
            if page > 0:
                # Some caches record 1-based pages while parsed_pages.jsonl uses 0-based indexes.
                cache.setdefault((source_file, page - 1), text)

    return cache


def get_cached_ocr_text(page_record: Dict, cache: Dict[Tuple[str, int], str]) -> str:
    try:
        page = int(page_record.get("page"))
    except (TypeError, ValueError):
        return ""
    return cache.get((page_record.get("source_file", ""), page), "")


def run_tesseract_ocr(page_record: Dict) -> str:
    if not ENABLE_OCR or shutil.which("tesseract") is None:
        return ""

    try:
        import fitz  # PyMuPDF
    except Exception:
        return ""

    source_path = Path(page_record["source_path"])
    page_index = int(page_record["page"])

    try:
        with fitz.open(source_path) as doc:
            page = doc[page_index]
            pix = page.get_pixmap(
                matrix=fitz.Matrix(OCR_RENDER_SCALE, OCR_RENDER_SCALE),
                alpha=False,
            )
            with tempfile.NamedTemporaryFile(suffix=".png") as img:
                pix.save(img.name)
                cp = subprocess.run(
                    ["tesseract", img.name, "stdout", "-l", OCR_LANG, "--psm", "6"],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=120,
                    check=False,
                )
        return normalize_text(cp.stdout)
    except Exception:
        return ""


def page_record_with_ocr_text(page_record: Dict, text: str, parse_method: str) -> Dict:
    updated = dict(page_record)
    updated["text"] = text
    updated["text_length"] = len(text)
    updated["parse_method"] = parse_method
    updated["needs_ocr"] = False
    updated["ocr_applied"] = True
    updated["originally_scanned_or_image_page"] = bool(
        page_record.get("is_scanned_or_image_page", False)
    )
    return updated


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_noise_line(line: str) -> bool:
    line = line.strip()

    if not line:
        return True

    # Page number or pure number line.
    if re.fullmatch(r"\d{1,4}", line):
        return True

    # Pure punctuation or symbols.
    if re.fullmatch(r"[\W_]+", line):
        return True

    # Single character or two-character fragments.
    if len(line) <= 2:
        if not re.search(r"[A-Za-z\u4e00-\u9fff]{2,}", line):
            return True

    # Numeric or symbolic table residue.
    if re.fullmatch(r"[\d\.\-\+\(\)\[\]\{\}:,; ]+", line):
        return True

    # Repeated symbols.
    if re.fullmatch(r"([~\-\_=:\.\*'`])\1{3,}", line):
        return True

    # Broken layout lines with too few useful characters.
    alpha_num = re.findall(r"[A-Za-z0-9\u4e00-\u9fff]", line)
    if len(line) >= 10:
        alpha_num_ratio = len(alpha_num) / max(len(line), 1)
        if alpha_num_ratio < 0.35:
            return True

    # Short isolated table fragments.
    short_noise_words = {
        "i", "o", "c", "e", "f", "n", "m", "p", "q",
        "vp", "pp", "tlb", "l1", "l2", "l3",
        "hit", "miss", "tag", "set", "byte", "word",
    }
    if line.lower() in short_noise_words and len(line) <= 4:
        return True

    # Common table fragments in CSAPP-like PDF extraction.
    table_fragment_patterns = [
        r"^cache hit\??",
        r"^cache byte",
        r"^byte returned",
        r"^address format",
        r"^set index",
        r"^tag bits?",
        r"^offset bits?",
        r"^parameter$",
        r"^value$",
        r"^\(?y\/n\)?$",
        r"^where cached$",
        r"^latency",
    ]

    lower_line = line.lower()
    for pattern in table_fragment_patterns:
        if re.search(pattern, lower_line):
            return True

    return False


def clean_extracted_text(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return ""

    cleaned_lines: List[str] = []
    blank_pending = False

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            blank_pending = True
            continue

        if is_noise_line(line):
            continue

        line = re.sub(r"\s+", " ", line).strip()

        if not line:
            continue

        if blank_pending and cleaned_lines and cleaned_lines[-1] != "":
            cleaned_lines.append("")

        blank_pending = False
        cleaned_lines.append(line)

    result_lines: List[str] = []
    for line in cleaned_lines:
        if line == "" and (not result_lines or result_lines[-1] == ""):
            continue
        result_lines.append(line)

    return "\n".join(result_lines).strip()


def looks_like_heading(line: str) -> bool:
    line = line.strip()
    lower = line.lower()

    if re.match(r"^(chapter|section|part)\s+\d+", lower):
        return True

    if re.match(r"^\d+(\.\d+)*\s+[A-Z][A-Za-z ]{3,}", line):
        return True

    return False


def split_paragraphs(text: str) -> List[str]:
    text = clean_extracted_text(text)
    if not text:
        return []

    raw_lines = text.splitlines()

    paragraphs: List[str] = []
    buffer: List[str] = []

    def flush():
        nonlocal buffer
        if buffer:
            para = " ".join(buffer).strip()
            para = re.sub(r"\s+", " ", para)
            if para:
                paragraphs.append(para)
            buffer = []

    for line in raw_lines:
        line = line.strip()

        if not line:
            flush()
            continue

        if looks_like_heading(line):
            flush()
            buffer.append(line)
            continue

        buffer.append(line)

        if re.search(r"[。！？.!?]$", line):
            flush()
        elif sum(len(x) for x in buffer) > 700:
            flush()

    flush()

    return [p for p in paragraphs if p.strip()]


def count_explanatory_sentences(text: str) -> int:
    parts = re.split(r"(?<=[。！？.!?])\s+", text)
    count = 0

    for p in parts:
        p = p.strip()
        if len(p) < 50:
            continue

        words = re.findall(r"[A-Za-z\u4e00-\u9fff]+", p)
        if len(words) >= 8:
            count += 1

    return count


def classify_chunk_role(text: str, reasons: List[str]) -> str:
    if "exercise_like_content" in reasons:
        return "exercise_or_problem"

    if "table_like_content" in reasons:
        return "table_or_layout_fragment"

    if "figure_like_content" in reasons:
        return "figure_or_caption"

    if "noisy_layout" in reasons:
        return "noisy_layout"

    explanatory_count = count_explanatory_sentences(text)

    if explanatory_count >= 2:
        return "explanatory_text"

    if explanatory_count == 1:
        return "short_explanatory_text"

    return "weak_semantic_text"


def assess_chunk_quality(text: str) -> Tuple[float, bool, List[str], str]:
    reasons: List[str] = []
    score = 1.0

    text = clean_extracted_text(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not text or not lines:
        return 0.0, True, ["empty_text"], "empty"

    text_len = len(text)
    line_count = len(lines)

    short_lines = [line for line in lines if len(line) <= 12]
    numeric_lines = [
        line for line in lines
        if re.fullmatch(r"[\d\.\-\+\(\)\[\]\{\}:,; ]+", line)
    ]

    alpha_chars = re.findall(r"[A-Za-z\u4e00-\u9fff]", text)
    digit_chars = re.findall(r"\d", text)

    short_line_ratio = len(short_lines) / max(line_count, 1)
    numeric_line_ratio = len(numeric_lines) / max(line_count, 1)
    alpha_ratio = len(alpha_chars) / max(text_len, 1)
    digit_ratio = len(digit_chars) / max(text_len, 1)
    avg_line_length = text_len / max(line_count, 1)
    explanatory_sentences = count_explanatory_sentences(text)

    lower_text = text.lower()

    exercise_patterns = [
        r"homework problem",
        r"practice problem",
        r"problem\s+\d+",
        r"exercise",
        r"exercises",
        r"quiz",
        r"indicate whether",
        r"fill in",
        r"answer the following",
        r"show your work",
        r"cache miss occurs",
    ]

    table_like_patterns = [
        r"address format",
        r"cache hit",
        r"byte returned",
        r"hexadecimal notation",
        r"tag bits",
        r"set index",
        r"offset bits",
        r"parameter\s+value",
        r"where cached",
        r"latency \(cycles\)",
    ]

    figure_like_patterns = [
        r"figure\s+\d+(\.\d+)?",
        r"table\s+\d+(\.\d+)?",
    ]

    code_or_output_patterns = [
        r"^\s*\$ ",
        r"^\s*>>>",
        r"^\s*0x[0-9a-f]+",
    ]

    if short_line_ratio > 0.40 and line_count >= 8:
        score -= 0.25
        reasons.append("short_line_ratio_high")

    if numeric_line_ratio > 0.15 and line_count >= 6:
        score -= 0.25
        reasons.append("many_numeric_lines")

    if alpha_ratio < 0.50:
        score -= 0.20
        reasons.append("low_alpha_ratio")

    if digit_ratio > 0.22:
        score -= 0.15
        reasons.append("digit_ratio_high")

    if avg_line_length < 30 and line_count >= 8:
        score -= 0.20
        reasons.append("avg_line_length_low")

    if explanatory_sentences == 0:
        score -= 0.25
        reasons.append("no_explanatory_sentence")

    for pattern in exercise_patterns:
        if re.search(pattern, lower_text):
            score -= 0.30
            reasons.append("exercise_like_content")
            break

    for pattern in table_like_patterns:
        if re.search(pattern, lower_text):
            score -= 0.25
            reasons.append("table_like_content")
            break

    for pattern in figure_like_patterns:
        if re.search(pattern, lower_text):
            score -= 0.15
            reasons.append("figure_like_content")
            break

    for pattern in code_or_output_patterns:
        if re.search(pattern, text, flags=re.MULTILINE):
            score -= 0.10
            reasons.append("code_or_terminal_like_content")
            break

    if text_len < 220:
        score -= 0.15
        reasons.append("too_short")

    if "short_line_ratio_high" in reasons and "many_numeric_lines" in reasons:
        score -= 0.15
        reasons.append("noisy_layout")

    if explanatory_sentences >= 2 and alpha_ratio >= 0.60:
        score += 0.20
        reasons.append("explanatory_rescue")

    score = max(0.0, min(1.0, score))
    content_role = classify_chunk_role(text, reasons)

    is_low_quality = (
        score < 0.60
        or content_role in {
            "exercise_or_problem",
            "table_or_layout_fragment",
            "figure_or_caption",
            "noisy_layout",
            "weak_semantic_text",
        }
    )

    return round(score, 3), is_low_quality, reasons, content_role


def build_chunks_for_page(page_record: Dict) -> List[Dict]:
    text = clean_extracted_text(page_record.get("text", ""))

    if not text:
        return []

    paragraphs = split_paragraphs(text)

    chunks: List[str] = []
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

    output: List[Dict] = []

    for idx, chunk_text in enumerate(chunks):
        cleaned_chunk_text = clean_extracted_text(chunk_text)
        if len(cleaned_chunk_text) < MIN_CHARS:
            continue

        quality_score, is_low_quality, quality_reasons, content_role = assess_chunk_quality(
            cleaned_chunk_text
        )

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
            "content_role": content_role,
            "parse_method": page_record.get("parse_method", "pymupdf_text"),
            "needs_ocr": bool(page_record.get("needs_ocr", False)),
            "ocr_applied": bool(page_record.get("ocr_applied", False)),
            "is_scanned_or_image_page": bool(page_record.get("is_scanned_or_image_page", False)),
            "originally_scanned_or_image_page": bool(
                page_record.get("originally_scanned_or_image_page", False)
            ),
            "citation_anchor": page_record["citation_anchor"],
            "text": cleaned_chunk_text,
            "text_length": len(cleaned_chunk_text),
            "chunk_index_in_page": idx,
            "quality_score": quality_score,
            "is_low_quality": is_low_quality,
            "quality_reasons": quality_reasons,
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
    ocr_todo_pages = 0
    ocr_chunked_pages = 0
    ocr_runtime_pages = 0
    total_chunks = 0
    low_quality_chunks = 0
    role_counter: Dict[str, int] = {}

    ocr_cache = load_ocr_cache(OCR_CACHE_PATHS)

    with CHUNK_OUTPUT_PATH.open("w", encoding="utf-8") as chunk_out, \
         OCR_TODO_PATH.open("w", encoding="utf-8") as ocr_out, \
         OCR_OUTPUT_PATH.open("a", encoding="utf-8") as ocr_cache_out:

        for page_record in load_jsonl(INPUT_PATH):
            total_pages += 1

            if page_record.get("needs_ocr"):
                cached_text = get_cached_ocr_text(page_record, ocr_cache)
                if cached_text:
                    page_record = page_record_with_ocr_text(
                        page_record,
                        cached_text,
                        "tesseract_ocr_cached",
                    )
                    ocr_chunked_pages += 1
                elif ENABLE_OCR and (OCR_MAX_PAGES <= 0 or ocr_runtime_pages < OCR_MAX_PAGES):
                    runtime_text = run_tesseract_ocr(page_record)
                    if runtime_text:
                        page_record = page_record_with_ocr_text(
                            page_record,
                            runtime_text,
                            "tesseract_ocr",
                        )
                        ocr_cache_out.write(json.dumps({
                            "source_file": page_record["source_file"],
                            "source_path": page_record["source_path"],
                            "discipline": page_record["discipline"],
                            "page": page_record["page"],
                            "text": runtime_text,
                            "text_length": len(runtime_text),
                            "parse_method": "tesseract_ocr",
                            "ocr_lang": OCR_LANG,
                        }, ensure_ascii=False) + "\n")
                        ocr_runtime_pages += 1
                        ocr_chunked_pages += 1

                if page_record.get("needs_ocr"):
                    ocr_todo_pages += 1
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
                if chunk.get("is_low_quality"):
                    low_quality_chunks += 1

                role = chunk.get("content_role", "unknown")
                role_counter[role] = role_counter.get(role, 0) + 1

                chunk_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                total_chunks += 1

    print("Text chunking finished.")
    print(f"Input pages: {total_pages}")
    print(f"Text/OCR chunked pages: {text_pages}")
    print(f"OCR pages converted to chunks: {ocr_chunked_pages}")
    print(f"OCR pages processed at runtime: {ocr_runtime_pages}")
    print(f"OCR todo pages: {ocr_todo_pages}")
    print(f"Generated chunks: {total_chunks}")
    print(f"Low-quality chunks: {low_quality_chunks}")
    print(f"High-quality chunks: {total_chunks - low_quality_chunks}")
    print("Content role summary:")
    for role, count in sorted(role_counter.items(), key=lambda x: x[1], reverse=True):
        print(f"  {role}: {count}")
    print(f"Chunk output: {CHUNK_OUTPUT_PATH}")
    print(f"OCR todo output: {OCR_TODO_PATH}")


if __name__ == "__main__":
    main()
