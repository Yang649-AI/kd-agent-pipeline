import json
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


def load_chunks(path: Path) -> List[Document]:
    docs = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            item = json.loads(line)

            text = item.get("text", "").strip()
            if not text:
                continue

            metadata = {
                "chunk_id": item.get("chunk_id"),
                "source_file": item.get("source_file"),
                "source_path": item.get("source_path"),
                "discipline": item.get("discipline"),
                "page": item.get("page"),
                "content_type": item.get("content_type"),
                "parse_method": item.get("parse_method"),
                "needs_ocr": item.get("needs_ocr"),
                "is_scanned_or_image_page": item.get("is_scanned_or_image_page"),
                "citation_anchor": item.get("citation_anchor"),
                "chunk_index_in_page": item.get("chunk_index_in_page"),
                "text_length": item.get("text_length"),
            }

            docs.append(Document(
                page_content=text,
                metadata=metadata,
            ))

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

    docs = load_chunks(CHUNK_PATH)

    if not docs:
        raise RuntimeError("No chunks loaded. Stop.")

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
    print(f"Collection name: {COLLECTION_NAME}")
    print(f"Saved to: {PERSIST_DIR}")


if __name__ == "__main__":
    main()
