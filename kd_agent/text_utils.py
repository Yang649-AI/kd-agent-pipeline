from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+\-/.]*|[\u4e00-\u9fff]|[0-9]+(?:\.[0-9]+)?")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def rough_token_count(text: str) -> int:
    tokens = tokenize(text)
    if tokens:
        return len(tokens)
    return max(1, math.ceil(len(text) / 4))


def keyword_overlap(a: str, b: str) -> int:
    left = set(tokenize(a))
    right = set(tokenize(b))
    return len(left & right)


def top_terms(text: str, limit: int = 12) -> list[str]:
    counts = Counter(t for t in tokenize(text) if len(t) > 1)
    return [term for term, _ in counts.most_common(limit)]


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[。！？.!?])\s+|\n+", text)
    return [c.strip() for c in chunks if c.strip()]


def unique_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
