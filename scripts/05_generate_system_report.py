import json
from pathlib import Path
import sys
from collections import Counter


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from common.paths import PROJECT_ROOT
from common.system_pipeline_paths import resolve_system_pipeline_paths

CHUNK_PATH = PROJECT_ROOT / "data" / "processed" / "text_chunks.jsonl"
OCR_TODO_PATH = PROJECT_ROOT / "data" / "processed" / "ocr_todo_pages.jsonl"


def load_jsonl(path: Path):
    if not path.exists():
        return []

    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def is_not_found_answer(answer: str) -> bool:
    if not answer:
        return True

    normalized = answer.strip().lower()

    not_found_patterns = [
        "未找到参考资料",
        "no supporting reference was found",
        "not found",
        "insufficient context",
        "cannot answer",
    ]

    return any(pattern in normalized for pattern in not_found_patterns)


def summarize_chunks(chunks):
    role_counter = Counter()
    reason_counter = Counter()

    total = len(chunks)
    low_quality = 0

    for item in chunks:
        role_counter[item.get("content_role", "unknown")] += 1

        if item.get("is_low_quality"):
            low_quality += 1
            for reason in item.get("quality_reasons", []):
                reason_counter[reason] += 1

    return {
        "total": total,
        "low_quality": low_quality,
        "high_quality": total - low_quality,
        "role_counter": role_counter,
        "reason_counter": reason_counter,
    }


def summarize_results(results):
    total = len(results)
    answered = 0
    not_found = 0
    retrieved_counts = []
    source_counter = Counter()

    for item in results:
        answer = item.get("answer", "")
        if is_not_found_answer(answer):
            not_found += 1
        else:
            answered += 1

        retrieved = item.get("retrieved", [])
        retrieved_counts.append(len(retrieved))

        for doc in retrieved:
            source_counter[doc.get("source_file", "unknown")] += 1

    avg_retrieved = 0.0
    if retrieved_counts:
        avg_retrieved = sum(retrieved_counts) / len(retrieved_counts)

    return {
        "total": total,
        "answered": answered,
        "not_found": not_found,
        "avg_retrieved": avg_retrieved,
        "source_counter": source_counter,
    }


def main():
    pipeline_paths = resolve_system_pipeline_paths()
    system_result_path = pipeline_paths.output_path
    report_path = pipeline_paths.report_path

    report_path.parent.mkdir(parents=True, exist_ok=True)

    results = load_jsonl(system_result_path)
    chunks = load_jsonl(CHUNK_PATH)
    ocr_todo = load_jsonl(OCR_TODO_PATH)

    if not results:
        raise FileNotFoundError(
            f"No system RAG result found at {system_result_path}. "
            "Please run scripts/run_system_rag.sh first."
        )

    result_summary = summarize_results(results)
    chunk_summary = summarize_chunks(chunks)

    lines = []
    lines.append("# System Pipeline Smoke Test Report")
    lines.append("")
    lines.append("## 1. Purpose")
    lines.append("")
    lines.append(
        "This report summarizes the current formal system pipeline validation. "
        "The pipeline includes PDF parsing, text chunking, chunk quality annotation, "
        "system vector index construction, RAG retrieval, answer generation, and citation output."
    )
    lines.append("")
    lines.append("## 2. Pipeline Components")
    lines.append("")
    lines.append("| Module | File | Status |")
    lines.append("|---|---|---|")
    lines.append("| PDF parser | `src/parser/parse_pdf_pages.py` | Completed |")
    lines.append("| Text chunker | `src/chunker/build_text_chunks.py` | Completed |")
    lines.append("| System indexer | `src/indexer/build_system_index.py` | Completed |")
    lines.append("| System RAG runner | `src/agent/run_system_rag.py` | Completed for smoke validation |")
    lines.append("| System config | `configs/system_config.yaml` | Completed |")
    lines.append("| System Modelfile template | `configs/Modelfile.system` | Completed |")
    lines.append("")
    lines.append("## 3. Data Processing Summary")
    lines.append("")
    lines.append(f"- Total text chunks: {chunk_summary['total']}")
    lines.append(f"- High-quality chunks: {chunk_summary['high_quality']}")
    lines.append(f"- Low-quality chunks: {chunk_summary['low_quality']}")
    lines.append(f"- OCR todo pages: {len(ocr_todo)}")
    lines.append("")
    lines.append("### Content Role Distribution")
    lines.append("")
    lines.append("| Content role | Count |")
    lines.append("|---|---:|")
    for role, count in chunk_summary["role_counter"].most_common():
        lines.append(f"| {role} | {count} |")
    lines.append("")
    lines.append("### Low-quality Reason Distribution")
    lines.append("")
    lines.append("| Reason | Count |")
    lines.append("|---|---:|")
    for reason, count in chunk_summary["reason_counter"].most_common():
        lines.append(f"| {reason} | {count} |")
    lines.append("")
    lines.append("## 4. System RAG Smoke Test Summary")
    lines.append("")
    lines.append(f"- Total questions: {result_summary['total']}")
    lines.append(f"- Answered questions: {result_summary['answered']}")
    lines.append(f"- Not-found answers: {result_summary['not_found']}")
    lines.append(f"- Average retrieved chunks per question: {result_summary['avg_retrieved']:.2f}")
    lines.append("")
    lines.append("### Retrieved Source Distribution")
    lines.append("")
    lines.append("| Source file | Retrieved count |")
    lines.append("|---|---:|")
    for source, count in result_summary["source_counter"].most_common():
        lines.append(f"| {source} | {count} |")
    lines.append("")
    lines.append("## 5. Question-level Results")
    lines.append("")
    lines.append("| ID | Question | Answer status | Retrieved chunks | First citation |")
    lines.append("|---|---|---|---:|---|")

    for item in results:
        qid = item.get("id", "")
        question = item.get("question", "").replace("|", "\\|")
        answer = item.get("answer", "")
        status = "not_found" if is_not_found_answer(answer) else "answered"
        retrieved = item.get("retrieved", [])
        retrieved_count = len(retrieved)

        first_citation = ""
        if retrieved:
            first = retrieved[0]
            first_citation = first.get("citation_anchor") or (
                f"{first.get('source_file', '')}: page {first.get('page', '')}"
            )
            first_citation = str(first_citation).replace("|", "\\|")

        lines.append(
            f"| {qid} | {question} | {status} | {retrieved_count} | {first_citation} |"
        )

    lines.append("")
    lines.append("## 6. Notes")
    lines.append("")
    lines.append(
        "- The current system RAG runner is used for pipeline validation. "
        "The formal target base model is Qwen3-VL-8B, as recorded in `configs/system_config.yaml`."
    )
    lines.append(
        "- Chunk quality fields are preserved in metadata, including `quality_score`, "
        "`is_low_quality`, `quality_reasons`, and `content_role`."
    )
    lines.append(
        "- Scanned or image-only PDF pages are recorded in the OCR todo list for later multimodal or OCR processing."
    )
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"System report generated: {report_path}")
    print(f"Questions: {result_summary['total']}")
    print(f"Answered: {result_summary['answered']}")
    print(f"Not found: {result_summary['not_found']}")
    print(f"Total chunks: {chunk_summary['total']}")
    print(f"High-quality chunks: {chunk_summary['high_quality']}")
    print(f"Low-quality chunks: {chunk_summary['low_quality']}")
    print(f"OCR todo pages: {len(ocr_todo)}")


if __name__ == "__main__":
    main()
