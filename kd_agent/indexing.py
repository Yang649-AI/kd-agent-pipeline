from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from .chunking import KnowledgeChunk
from .text_utils import tokenize


class LocalTfidfIndex:
    def __init__(self, chunks: list[KnowledgeChunk], idf: dict[str, float] | None = None) -> None:
        self.chunks = chunks
        self.idf = idf or self._build_idf(chunks)
        self._vectors = [self._vector(c.text + " " + " ".join(c.keywords)) for c in chunks]
        self._norms = [math.sqrt(sum(v * v for v in vec.values())) or 1.0 for vec in self._vectors]

    @staticmethod
    def _build_idf(chunks: list[KnowledgeChunk]) -> dict[str, float]:
        df: dict[str, int] = defaultdict(int)
        for chunk in chunks:
            for term in set(tokenize(chunk.text)):
                df[term] += 1
        total = max(1, len(chunks))
        return {term: math.log((1 + total) / (1 + freq)) + 1.0 for term, freq in df.items()}

    def _vector(self, text: str) -> dict[str, float]:
        counts = Counter(tokenize(text))
        return {term: (1 + math.log(freq)) * self.idf.get(term, 1.0) for term, freq in counts.items() if freq > 0}

    def search(self, query: str, top_k: int = 5) -> list[tuple[KnowledgeChunk, float]]:
        qvec = self._vector(query)
        qnorm = math.sqrt(sum(v * v for v in qvec.values())) or 1.0
        scored: list[tuple[KnowledgeChunk, float]] = []
        for chunk, vec, norm in zip(self.chunks, self._vectors, self._norms):
            dot = sum(weight * vec.get(term, 0.0) for term, weight in qvec.items())
            score = dot / (qnorm * norm)
            scored.append((chunk, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "idf": self.idf,
            "chunks": [asdict(chunk) for chunk in self.chunks],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "LocalTfidfIndex":
        chunks = [KnowledgeChunk(**item) for item in payload["chunks"]]
        return cls(chunks, idf=payload.get("idf"))


def save_index(index: LocalTfidfIndex, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def load_index(path: Path) -> LocalTfidfIndex:
    return LocalTfidfIndex.from_dict(json.loads(path.read_text(encoding="utf-8")))
