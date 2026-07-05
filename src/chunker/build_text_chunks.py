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
            "is_scanned_or_image_page": bool(page_record.get("is_scanned_or_image_page", False)),
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
    ocr_pages = 0
    total_chunks = 0
    low_quality_chunks = 0
    role_counter: Dict[str, int] = {}

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
                if chunk.get("is_low_quality"):
                    low_quality_chunks += 1

                role = chunk.get("content_role", "unknown")
                role_counter[role] = role_counter.get(role, 0) + 1

                chunk_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                total_chunks += 1

    print("Text chunking finished.")
    print(f"Input pages: {total_pages}")
    print(f"Text pages: {text_pages}")
    print(f"OCR todo pages: {ocr_pages}")
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