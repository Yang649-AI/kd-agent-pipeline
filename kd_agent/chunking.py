from __future__ import annotations

import re
from dataclasses import dataclass, field

from .ingestion import ParsedDocument
from .text_utils import rough_token_count, split_sentences, top_terms


@dataclass
class KnowledgeChunk:
    chunk_id: str
    doc_id: str
    source_file: str
    discipline: str
    modality: str
    title_path: list[str]
    text: str
    token_count: int
    keywords: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def citation(self) -> str:
        page = self.metadata.get("page")
        page_part = f":p{page}" if page else ""
        return f"{self.source_file}{page_part}#{self.chunk_id}"


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")


def _sections_from_markdown(text: str) -> list[tuple[list[str], str]]:
    sections: list[tuple[list[str], list[str]]] = []
    current_titles: list[str] = []
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines:
            sections.append((current_titles[:], current_lines[:]))
            current_lines.clear()

    for line in text.splitlines():
        m = HEADING_RE.match(line.strip())
        if m:
            flush()
            level = len(m.group(1))
            current_titles[:] = current_titles[: level - 1] + [m.group(2).strip()]
            current_lines.append(line)
        else:
            current_lines.append(line)
    flush()

    if not sections:
        return [([], text)]
    return [(titles, "\n".join(lines).strip()) for titles, lines in sections if "\n".join(lines).strip()]


def adaptive_chunk_documents(
    docs: list[ParsedDocument],
    target_tokens: int = 360,
    min_tokens: int = 120,
    overlap_tokens: int = 40,
) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for doc in docs:
        sections = _sections_from_markdown(doc.text)
        chunk_no = 0
        for title_path, section in sections:
            sentences = split_sentences(section)
            buffer: list[str] = []
            buffer_tokens = 0

            def emit(force: bool = False) -> None:
                nonlocal chunk_no, buffer, buffer_tokens
                if not buffer:
                    return
                if not force and buffer_tokens < min_tokens:
                    return
                chunk_no += 1
                text = "\n".join(buffer).strip()
                chunk_id = f"{doc.doc_id}:c{chunk_no:03d}"
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=chunk_id,
                        doc_id=doc.doc_id,
                        source_file=doc.source_file,
                        discipline=doc.discipline,
                        modality=doc.modality,
                        title_path=title_path,
                        text=text,
                        token_count=rough_token_count(text),
                        keywords=top_terms(text),
                        metadata=dict(doc.metadata),
                    )
                )
                if overlap_tokens > 0:
                    kept: list[str] = []
                    kept_tokens = 0
                    for sent in reversed(buffer):
                        sent_tokens = rough_token_count(sent)
                        if kept_tokens + sent_tokens > overlap_tokens:
                            break
                        kept.insert(0, sent)
                        kept_tokens += sent_tokens
                    buffer = kept
                    buffer_tokens = kept_tokens
                else:
                    buffer = []
                    buffer_tokens = 0

            for sent in sentences:
                sent_tokens = rough_token_count(sent)
                if buffer and buffer_tokens + sent_tokens > target_tokens:
                    emit(force=True)
                buffer.append(sent)
                buffer_tokens += sent_tokens
            emit(force=True)
    return chunks


def _sentence_vector(sentence: str) -> dict[str, float]:
    from collections import Counter
    import math

    tokens = [t for t in top_terms(sentence, limit=64)]
    counts = Counter(tokens)
    norm = math.sqrt(sum(v * v for v in counts.values())) or 1.0
    return {k: v / norm for k, v in counts.items()}


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return sum(weight * right.get(term, 0.0) for term, weight in left.items())


def _semantic_breaks(sentences: list[str], window_size: int = 2, percentile: float = 0.30) -> set[int]:
    """Return sentence indexes where a new semantic chunk should start.

    The implementation is intentionally local and offline: it compares adjacent
    sentence windows with normalized lexical vectors. If sentence-transformer
    embeddings are later available, this function can be replaced without
    changing the chunk output contract.
    """
    if len(sentences) < 4:
        return set()

    scores: list[tuple[int, float]] = []
    for i in range(1, len(sentences)):
        left = " ".join(sentences[max(0, i - window_size):i])
        right = " ".join(sentences[i:min(len(sentences), i + window_size)])
        scores.append((i, _cosine(_sentence_vector(left), _sentence_vector(right))))

    ordered = sorted(score for _, score in scores)
    threshold_index = max(0, min(len(ordered) - 1, int(len(ordered) * percentile)))
    threshold = ordered[threshold_index]
    return {idx for idx, score in scores if score <= threshold}


def semantic_chunk_documents(
    docs: list[ParsedDocument],
    target_tokens: int = 360,
    min_tokens: int = 120,
    max_tokens: int | None = None,
    overlap_tokens: int = 40,
    similarity_percentile: float = 0.30,
) -> list[KnowledgeChunk]:
    """Chunk documents by semantic boundary detection plus token budgets."""
    max_tokens = max_tokens or int(target_tokens * 1.45)
    chunks: list[KnowledgeChunk] = []

    for doc in docs:
        sections = _sections_from_markdown(doc.text)
        chunk_no = 0
        for title_path, section in sections:
            sentences = split_sentences(section)
            breaks = _semantic_breaks(sentences, percentile=similarity_percentile)
            buffer: list[str] = []
            buffer_tokens = 0

            def emit(force: bool = False) -> None:
                nonlocal chunk_no, buffer, buffer_tokens
                if not buffer:
                    return
                if not force and buffer_tokens < min_tokens:
                    return
                chunk_no += 1
                text = "\n".join(buffer).strip()
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=f"{doc.doc_id}:sc{chunk_no:03d}",
                        doc_id=doc.doc_id,
                        source_file=doc.source_file,
                        discipline=doc.discipline,
                        modality=doc.modality,
                        title_path=title_path,
                        text=text,
                        token_count=rough_token_count(text),
                        keywords=top_terms(text),
                        metadata={**dict(doc.metadata), "chunking": "semantic_lexical_boundary"},
                    )
                )
                if overlap_tokens > 0:
                    kept: list[str] = []
                    kept_tokens = 0
                    for sent in reversed(buffer):
                        sent_tokens = rough_token_count(sent)
                        if kept_tokens + sent_tokens > overlap_tokens:
                            break
                        kept.insert(0, sent)
                        kept_tokens += sent_tokens
                    buffer = kept
                    buffer_tokens = kept_tokens
                else:
                    buffer = []
                    buffer_tokens = 0

            for i, sent in enumerate(sentences):
                sent_tokens = rough_token_count(sent)
                should_break = i in breaks and buffer_tokens >= min_tokens
                too_large = buffer and buffer_tokens + sent_tokens > max_tokens
                if should_break or too_large:
                    emit(force=True)
                buffer.append(sent)
                buffer_tokens += sent_tokens
                if buffer_tokens >= target_tokens and i + 1 in breaks:
                    emit(force=True)
            emit(force=True)

    return chunks
