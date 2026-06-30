from pathlib import Path
from tqdm import tqdm

import torch
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


PROJECT_ROOT = Path("/root/autodl-tmp/kd_agent_pipeline")
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PERSIST_DIR = str(PROJECT_ROOT / "data" / "indexes" / "chroma_baseline")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
COLLECTION_NAME = "baseline_rag"


def load_pdfs(raw_dir: Path):
    docs = []
    pdf_files = list(raw_dir.rglob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in: {raw_dir}")
        print("Please put PDF files into:")
        print("  data/raw/cs/")
        print("  data/raw/medicine/")
        print("  data/raw/law/")
        return docs

    for pdf_path in tqdm(pdf_files, desc="Loading PDFs"):
        loader = PyMuPDFLoader(str(pdf_path))
        loaded_docs = loader.load()

        for doc in loaded_docs:
            doc.metadata["source_file"] = pdf_path.name
            doc.metadata["source_path"] = str(pdf_path)
            doc.metadata["discipline"] = pdf_path.parent.name

        docs.extend(loaded_docs)

    return docs


def main():
    print("Building baseline vector index...")
    print(f"Raw data dir: {RAW_DIR}")
    print(f"Persist dir: {PERSIST_DIR}")

    docs = load_pdfs(RAW_DIR)

    if not docs:
        print("No documents loaded. Stop.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )

    chunks = splitter.split_documents(docs)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Embedding device: {device}")

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-zh-v1.5",
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME,
    )

    print("Baseline index created successfully.")
    print(f"Loaded pages/docs: {len(docs)}")
    print(f"Created chunks: {len(chunks)}")
    print(f"Vector store saved to: {PERSIST_DIR}")


if __name__ == "__main__":
    main()
