from __future__ import annotations

import json
import time
from pathlib import Path

from .agent import answer_question
from .config import PipelineConfig
from .indexing import load_index


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _hit_at_k(retrieved: list[dict], expected_chunk_ids: list[str]) -> bool:
    if not expected_chunk_ids:
        return False
    retrieved_ids = {item.get("chunk_id") for item in retrieved}
    return bool(retrieved_ids & set(expected_chunk_ids))


def _has_required_answer_terms(answer: str, terms: list[str]) -> bool:
    return all(term.lower() in answer.lower() for term in terms)


def run_evaluation(config: PipelineConfig) -> dict:
    index = load_index(config.index_path)
    questions = load_jsonl(config.eval_path)
    config.results_path.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    with config.results_path.open("w", encoding="utf-8") as out:
        for item in questions:
            started = time.perf_counter()
            result = answer_question(
                index=index,
                question=item["question"],
                top_k=config.top_k,
                context_tokens=config.compressed_context_tokens,
            )
            latency = time.perf_counter() - started
            row = {
                "id": item["id"],
                "discipline": item.get("discipline", config.discipline),
                "question": item["question"],
                "expected_chunk_ids": item.get("expected_chunk_ids", []),
                "answer_terms": item.get("answer_terms", []),
                "answer": result.answer,
                "citations": result.citations,
                "retrieved": result.retrieved,
                "latency_sec": latency,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "total_tokens": result.total_tokens,
                "compression_ratio": result.compression_ratio,
                "hit_at_5": _hit_at_k(result.retrieved, item.get("expected_chunk_ids", [])),
                "answer_term_match": _has_required_answer_terms(result.answer, item.get("answer_terms", [])),
                "unsupported_generation": result.answer != "未找到参考资料" and not result.citations,
            }
            results.append(row)
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    num = max(1, len(results))
    metrics = {
        "system_name": "Adaptive Distillation RAG + Citation Agent",
        "discipline": config.discipline,
        "num_questions": len(results),
        "hit_at_5": sum(1 for r in results if r["hit_at_5"]) / num,
        "answer_term_accuracy": sum(1 for r in results if r["answer_term_match"]) / num,
        "hallucination_rate_no_citation": sum(1 for r in results if r["unsupported_generation"]) / num,
        "avg_latency_sec": sum(r["latency_sec"] for r in results) / num,
        "avg_input_tokens": sum(r["input_tokens"] for r in results) / num,
        "avg_output_tokens": sum(r["output_tokens"] for r in results) / num,
        "avg_total_tokens": sum(r["total_tokens"] for r in results) / num,
        "sum_total_tokens": sum(r["total_tokens"] for r in results),
        "avg_context_compression_ratio": sum(r["compression_ratio"] for r in results) / num,
        "top_k": config.top_k,
        "adaptive_chunking": True,
        "context_compression": True,
        "citation_grounding": True,
        "rerank": "tfidf_keyword_scoring",
        "lora": False,
    }
    config.metrics_path.parent.mkdir(parents=True, exist_ok=True)
    config.metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return metrics
