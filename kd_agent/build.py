from __future__ import annotations

from .agent import write_agent_config
from .chunking import adaptive_chunk_documents
from .config import PipelineConfig
from .indexing import LocalTfidfIndex, save_index
from .ingestion import load_documents


def build_index(config: PipelineConfig) -> dict:
    docs = load_documents(config.raw_dirs, discipline=config.discipline)
    if not docs:
        raise RuntimeError(f"No documents found under: {', '.join(str(p) for p in config.raw_dirs)}")
    chunks = adaptive_chunk_documents(
        docs,
        target_tokens=config.chunk_target_tokens,
        min_tokens=config.chunk_min_tokens,
        overlap_tokens=config.chunk_overlap_tokens,
    )
    index = LocalTfidfIndex(chunks)
    save_index(index, config.index_path)
    write_agent_config(config.agent_config_path)
    return {
        "num_documents": len(docs),
        "num_chunks": len(chunks),
        "index_path": str(config.index_path),
        "agent_config_path": str(config.agent_config_path),
    }
