from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

from .text_utils import normalize_space


@dataclass
class ParsedDocument:
    doc_id: str
    source_path: str
    source_file: str
    discipline: str
    modality: str
    text: str
    metadata: dict = field(default_factory=dict)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return "\n".join(self.parts)


def _read_pdf(path: Path) -> list[tuple[str, dict]]:
    try:
        import fitz  # type: ignore
    except Exception:
        return [("", {"parser_warning": "PyMuPDF not installed; PDF text extraction skipped."})]

    rows: list[tuple[str, dict]] = []
    with fitz.open(path) as doc:
        for page_no, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            rows.append((text, {"page": page_no}))
    return rows


def _read_epub(path: Path) -> str:
    texts: list[str] = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if name.lower().endswith((".xhtml", ".html", ".htm")):
                parser = _HTMLTextExtractor()
                parser.feed(zf.read(name).decode("utf-8", errors="ignore"))
                texts.append(parser.text())
    return "\n\n".join(texts)


def _read_jsonl(path: Path) -> str:
    parts: list[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            obj = json.loads(line)
            parts.append(obj.get("text") or obj.get("content") or json.dumps(obj, ensure_ascii=False))
    return "\n\n".join(parts)


def _clean_text(text: str, preserve_lines: bool) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not preserve_lines:
        return normalize_space(text)
    lines = [normalize_space(line) for line in text.splitlines()]
    collapsed: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if not blank:
                collapsed.append("")
            blank = True
        else:
            collapsed.append(line)
            blank = False
    return "\n".join(collapsed).strip()


def parse_file(path: Path, discipline: str) -> list[ParsedDocument]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        docs = []
        for i, (text, meta) in enumerate(_read_pdf(path), start=1):
            if text.strip():
                docs.append(
                    ParsedDocument(
                        doc_id=f"{path.stem}:p{i}",
                        source_path=str(path),
                        source_file=path.name,
                        discipline=discipline,
                        modality="pdf",
                        text=text,
                        metadata=meta,
                    )
                )
        return docs

    preserve_lines = suffix in {".md", ".txt"}
    if suffix in {".md", ".txt"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        modality = "markdown" if suffix == ".md" else "text"
    elif suffix == ".jsonl":
        text = _read_jsonl(path)
        modality = "jsonl"
    elif suffix == ".epub":
        text = _read_epub(path)
        modality = "epub"
    elif suffix in {".png", ".jpg", ".jpeg", ".svg"}:
        text = f"[图像占位] 文件 {path.name} 已登记。正式环境可接入本地 OCR/VLM 提取图表、公式、坐标和表格结构。"
        modality = "image"
    elif suffix in {".mp3", ".wav", ".flac", ".m4a"}:
        text = f"[音频占位] 文件 {path.name} 已登记。正式环境可接入 whisper.cpp 或 faster-whisper 进行本地 ASR、时间戳对齐和说话人分离。"
        modality = "audio"
    else:
        return []

    text = _clean_text(text, preserve_lines=preserve_lines)
    if not text:
        return []
    return [
        ParsedDocument(
            doc_id=path.stem,
            source_path=str(path),
            source_file=path.name,
            discipline=discipline,
            modality=modality,
            text=text,
            metadata={},
        )
    ]


def load_documents(raw_dirs: Iterable[Path], discipline: str) -> list[ParsedDocument]:
    supported = {".pdf", ".md", ".txt", ".jsonl", ".epub", ".png", ".jpg", ".jpeg", ".svg", ".mp3", ".wav", ".flac", ".m4a"}
    docs: list[ParsedDocument] = []
    for raw_dir in raw_dirs:
        if not raw_dir.exists():
            continue
        for path in sorted(p for p in raw_dir.rglob("*") if p.is_file() and p.suffix.lower() in supported):
            docs.extend(parse_file(path, discipline=discipline))
    return docs
