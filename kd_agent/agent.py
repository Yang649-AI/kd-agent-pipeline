from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .chunking import KnowledgeChunk
from .indexing import LocalTfidfIndex
from .text_utils import keyword_overlap, rough_token_count, split_sentences, unique_preserve_order


@dataclass
class AnswerResult:
    answer: str
    citations: list[str]
    retrieved: list[dict]
    input_tokens: int
    output_tokens: int
    total_tokens: int
    compression_ratio: float


SYSTEM_PROMPT = """你是一个可本地运行的计算机学科知识智能体。
规则：
1. 只依据检索资料回答。
2. 每个关键结论必须带引用锚点，例如 [S1]。
3. 如果资料不足，回答“未找到参考资料”。
4. 不输出思考过程。
"""


def compress_context(question: str, chunks: list[KnowledgeChunk], max_tokens: int) -> tuple[str, list[str]]:
    selected: list[str] = []
    citations: list[str] = []
    used = 0
    for i, chunk in enumerate(chunks, start=1):
        sentence_scores = sorted(
            ((keyword_overlap(question, sent), sent) for sent in split_sentences(chunk.text)),
            key=lambda item: item[0],
            reverse=True,
        )
        best = [sent for score, sent in sentence_scores if score > 0][:3]
        if not best:
            best = split_sentences(chunk.text)[:2]
        citation = f"S{i}"
        context_piece = f"[{citation}] {chunk.citation()}\n" + " ".join(best)
        piece_tokens = rough_token_count(context_piece)
        if selected and used + piece_tokens > max_tokens:
            continue
        selected.append(context_piece)
        citations.append(citation)
        used += piece_tokens
    return "\n\n".join(selected), citations


def _is_evidence_sentence(sentence: str) -> bool:
    stripped = sentence.strip()
    if not stripped or stripped.lstrip().startswith("#"):
        return False
    if len(stripped) < 18:
        return False
    alnum = sum(1 for ch in stripped if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")
    if alnum / max(1, len(stripped)) < 0.35:
        return False
    heading_markers = ("section ", "chapter ", "preface", "bibliographic notes", "homework problems")
    lower = stripped.lower()
    if any(lower == marker.strip() or lower.startswith(marker) and len(stripped) < 80 for marker in heading_markers):
        return False
    return True


def grounded_extractive_answer(question: str, chunks: list[KnowledgeChunk]) -> str:
    candidates: list[tuple[int, int, int, str]] = []
    for source_no, chunk in enumerate(chunks, start=1):
        for sent_no, sent in enumerate(split_sentences(chunk.text)):
            if not _is_evidence_sentence(sent):
                continue
            score = keyword_overlap(question, sent)
            title_score = keyword_overlap(question, " ".join(chunk.title_path))
            if score > 0 or title_score > 0:
                candidates.append((score + title_score, -source_no, -sent_no, sent.strip()))

    if not candidates:
        return "未找到参考资料"

    candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    answer_sents: list[str] = []
    for _, neg_source_no, _, sent in candidates:
        source_no = -neg_source_no
        rendered = f"{sent} [S{source_no}]"
        if rendered not in answer_sents:
            answer_sents.append(rendered)
        if len(answer_sents) >= 3:
            break
    return " ".join(answer_sents) if answer_sents else "未找到参考资料"


def answer_question(index: LocalTfidfIndex, question: str, top_k: int = 5, context_tokens: int = 900) -> AnswerResult:
    scored = index.search(question, top_k=top_k)
    chunks = [chunk for chunk, _ in scored]
    raw_context = "\n\n".join(chunk.text for chunk in chunks)
    context, citation_labels = compress_context(question, chunks, max_tokens=context_tokens)
    answer = grounded_extractive_answer(question, chunks)

    if answer != "未找到参考资料":
        citations = [f"S{i}" for i in range(1, len(chunks) + 1) if f"[S{i}]" in answer]
    else:
        citations = []

    prompt_text = f"{SYSTEM_PROMPT}\n问题：{question}\n资料：\n{context}\n回答："
    input_tokens = rough_token_count(prompt_text)
    output_tokens = rough_token_count(answer)
    raw_tokens = rough_token_count(raw_context) or 1
    compressed_tokens = rough_token_count(context)

    return AnswerResult(
        answer=answer,
        citations=citations or citation_labels[:1] if answer != "未找到参考资料" else [],
        retrieved=[
            {
                "rank": rank,
                "score": round(score, 6),
                "chunk_id": chunk.chunk_id,
                "source_file": chunk.source_file,
                "citation": chunk.citation(),
                "title_path": chunk.title_path,
                "keywords": chunk.keywords,
                "content_preview": chunk.text[:260],
            }
            for rank, (chunk, score) in enumerate(scored, start=1)
        ],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        compression_ratio=compressed_tokens / raw_tokens,
    )


def write_agent_config(path: Path, model_name: str = "qwen3-vl-8b-kd-agent") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "agent_name": "cs-kd-agent",
        "discipline": "cs",
        "runtime": "ollama-compatible",
        "model": model_name,
        "system_prompt": SYSTEM_PROMPT,
        "tools": [
            {"name": "local_tfidf_retriever", "description": "Top-K citation grounded local retrieval over distilled chunks."},
            {"name": "context_compressor", "description": "Question-aware sentence compression before generation."},
            {"name": "citation_guard", "description": "Reject unsupported answers and require source anchors."},
        ],
        "generation": {"temperature": 0, "num_ctx": 4096},
        "retrieval": {"top_k": 5, "context_budget_tokens": 900},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
