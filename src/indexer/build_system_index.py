import json
import os
import shutil
from pathlib import Path
from typing import List

import torch
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


PROJECT_ROOT = Path("/root/autodl-tmp/kd_agent_pipeline")

CHUNK_PATH = PROJECT_ROOT / "data" / "processed" / "text_chunks.jsonl"
PERSIST_DIR = PROJECT_ROOT / "data" / "indexes" / "chroma_system"

COLLECTION_NAME = "system_rag"
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

INCLUDE_LOW_QUALITY = os.getenv("INCLUDE_LOW_QUALITY", "0") == "1"

ALLOWED_CONTENT_ROLES = {
    "explanatory_text",
    "short_explanatory_text",
    "figure_or_caption",
    "weak_semantic_text",
    "table_or_layout_fragment",
    "exercise_or_problem",
    "noisy_layout",
}


def safe_metadata_value(value):
    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, list):
        return ";".join(str(x) for x in value)

    return str(value)


def load_chunks(path: Path) -> List[Document]:
    docs: List[Document] = []

    total_chunks = 0
    empty_chunks = 0
    low_quality_skipped = 0
    role_skipped = 0
    selected_by_role = {}

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            total_chunks += 1
            item = json.loads(line)

            text = item.get("text", "").strip()
            if not text:
                empty_chunks += 1
                continue

            is_low_quality = bool(item.get("is_low_quality", False))
            content_role = item.get("content_role", "")

            if is_low_quality and not INCLUDE_LOW_QUALITY:
                low_quality_skipped += 1
                continue

            if content_role and content_role not in ALLOWED_CONTENT_ROLES:
                role_skipped += 1
                continue

            selected_by_role[content_role] = selected_by_role.get(content_role, 0) + 1

            metadata = {
                "chunk_id": safe_metadata_value(item.get("chunk_id")),
                "source_file": safe_metadata_value(item.get("source_file")),
                "source_path": safe_metadata_value(item.get("source_path")),
                "discipline": safe_metadata_value(item.get("discipline")),
                "page": safe_metadata_value(item.get("page")),
                "content_type": safe_metadata_value(item.get("content_type")),
                "content_role": safe_metadata_value(item.get("content_role")),
                "parse_method": safe_metadata_value(item.get("parse_method")),
                "needs_ocr": safe_metadata_value(item.get("needs_ocr")),
                "ocr_applied": safe_metadata_value(item.get("ocr_applied")),
                "is_scanned_or_image_page": safe_metadata_value(item.get("is_scanned_or_image_page")),
                "originally_scanned_or_image_page": safe_metadata_value(item.get("originally_scanned_or_image_page")),
                "citation_anchor": safe_metadata_value(item.get("citation_anchor")),
                "chunk_index_in_page": safe_metadata_value(item.get("chunk_index_in_page")),
                "text_length": safe_metadata_value(item.get("text_length")),
                "quality_score": safe_metadata_value(item.get("quality_score")),
                "is_low_quality": safe_metadata_value(item.get("is_low_quality")),
                "quality_reasons": safe_metadata_value(item.get("quality_reasons")),
            }

            docs.append(Document(
                page_content=text,
                metadata=metadata,
            ))

    print("Chunk loading summary:")
    print(f"  Total chunks in file: {total_chunks}")
    print(f"  Empty chunks skipped: {empty_chunks}")
    print(f"  Low-quality chunks skipped: {low_quality_skipped}")
    print(f"  Content-role chunks skipped: {role_skipped}")
    print(f"  Chunks selected for indexing: {len(docs)}")
    print(f"  INCLUDE_LOW_QUALITY: {INCLUDE_LOW_QUALITY}")
    print("  Selected content roles:")
    for role, count in sorted(selected_by_role.items(), key=lambda x: x[1], reverse=True):
        print(f"    {role}: {count}")

    return docs


def main():
    if not CHUNK_PATH.exists():
        raise FileNotFoundError(
            f"Chunk file not found: {CHUNK_PATH}. "
            "Please run src/parser/parse_pdf_pages.py and "
            "src/chunker/build_text_chunks.py first."
        )

    print("Building system vector index...")
    print(f"Chunk file: {CHUNK_PATH}")
    print(f"Persist dir: {PERSIST_DIR}")
    print(f"Collection name: {COLLECTION_NAME}")
    print(f"Allowed content roles: {sorted(ALLOWED_CONTENT_ROLES)}")

    docs = load_chunks(CHUNK_PATH)

    if not docs:
        raise RuntimeError(
            "No chunks loaded for indexing. "
            "Check whether all chunks were marked as low quality or filtered by content_role."
        )

    if PERSIST_DIR.exists():
        print(f"Removing existing index: {PERSIST_DIR}")
        shutil.rmtree(PERSIST_DIR)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Embedding device: {device}")
    print(f"Embedding model: {EMBEDDING_MODEL}")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )

    Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=str(PERSIST_DIR),
        collection_name=COLLECTION_NAME,
    )

    print("System index created successfully.")
    print(f"Indexed chunks: {len(docs)}")
    print(f"Saved to: {PERSIST_DIR}")


if __name__ == "__main__":
    main()