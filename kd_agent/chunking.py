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
