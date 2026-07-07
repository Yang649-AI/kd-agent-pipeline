import json
import time
from pathlib import Path
import sys

import torch
from transformers import AutoTokenizer

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.system_fallback import build_extractive_fallback_answer
from agent.answer_postprocess import clean_ollama_answer
from common.console_text import sanitize_for_console
from common.paths import PROJECT_ROOT
from common.system_pipeline_paths import resolve_system_pipeline_paths

PERSIST_DIR = str(PROJECT_ROOT / "data" / "indexes" / "chroma_system")

MODEL_NAME = "qwen-8b-instruct-baseline"
TOP_K = 4

SYSTEM_PROMPT = """You are a vertical-domain agent grounded only in local documents.

Answer only from the retrieved context. Do not use outside knowledge.

Rules:
1. If any retrieved passage contains a sentence that directly answers the question, answer briefly from that passage and cite source file plus page.
2. Treat a passage as supporting evidence when it directly contains the requested fact, even if the wording differs from the question.
3. If the retrieved context is unrelated to the question or does not contain the requested fact, output exactly:
Answer:
No supporting reference found.
References:
- No supporting reference found.
4. Use the same language as the question when the context supports an answer.
5. Do not invent facts that are absent from the retrieved context.
6. Do not output chain-of-thought, reasoning tags, /think, or </think>.

Question:
{question}

Retrieved context:
{context}

Return only this format:
Answer:
References:
"""


def load_eval_questions(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def format_docs(docs):
    parts = []

    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata

        source = meta.get("source_file", "")
        page = meta.get("page", "")
        anchor = meta.get("citation_anchor", "")
        chunk_id = meta.get("chunk_id", "")
        content_type = meta.get("content_type", "")
        text = doc.page_content

        parts.append(
            f"[{i}]\n"
            f"Source file: {source}\n"
            f"Page: {page}\n"
            f"Citation anchor: {anchor}\n"
            f"Chunk ID: {chunk_id}\n"
            f"Content type: {content_type}\n"
            f"Text:\n{text}"
        )

    return "\n\n".join(parts)


def safe_count_tokens(text: str, tokenizer):
    try:
        return len(tokenizer.encode(text))
    except Exception:
        return int(len(text) / 1.5)


def main():
    pipeline_paths = resolve_system_pipeline_paths()
    eval_path = pipeline_paths.eval_path
    output_path = pipeline_paths.output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Loading tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen3-8B",
            trust_remote_code=True,
            cache_dir=str(PROJECT_ROOT / "cache" / "huggingface"),
        )
    except Exception as e:
        print("Tokenizer loading failed, fallback to rough token estimation.")
        print("Reason:", repr(e))
        tokenizer = None

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Embedding device:", device)

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-zh-v1.5",
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )

    vectordb = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings,
        collection_name="system_rag",
    )

    retriever = vectordb.as_retriever(search_kwargs={"k": TOP_K})

    llm = ChatOllama(
        model=MODEL_NAME,
        temperature=0,
        num_ctx=4096,
    )
    use_fallback_only = False

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    with output_path.open("w", encoding="utf-8") as out:
        for item in load_eval_questions(eval_path):
            question = item["question"]
            print(f"\nRunning system RAG question: {item['id']}")

            start = time.perf_counter()

            docs = retriever.invoke(question)
            context = format_docs(docs)

            prompt_text = SYSTEM_PROMPT.format(
                question=question,
                context=context,
            )

            messages = prompt.invoke({
                "question": question,
                "context": context,
            })

            if use_fallback_only:
                answer = build_extractive_fallback_answer(docs)
                response_mode = "extractive_fallback"
            else:
                try:
                    response = llm.invoke(messages)
                    answer = clean_ollama_answer(response.content)
                    response_mode = "ollama"
                except Exception as exc:
                    print(
                        "Ollama invocation failed, switching to extractive fallback. "
                        f"Reason: {exc!r}"
                    )
                    use_fallback_only = True
                    answer = build_extractive_fallback_answer(docs)
                    response_mode = "extractive_fallback"

            elapsed = time.perf_counter() - start

            if tokenizer is not None:
                input_tokens = safe_count_tokens(prompt_text, tokenizer)
                output_tokens = safe_count_tokens(answer, tokenizer)
            else:
                input_tokens = int(len(prompt_text) / 1.5)
                output_tokens = int(len(answer) / 1.5)

            total_tokens = input_tokens + output_tokens

            retrieved = []
            for doc in docs:
                meta = doc.metadata
                retrieved.append({
                    "chunk_id": meta.get("chunk_id"),
                    "source_file": meta.get("source_file"),
                    "page": meta.get("page"),
                    "discipline": meta.get("discipline"),
                    "content_type": meta.get("content_type"),
                    "citation_anchor": meta.get("citation_anchor"),
                    "text_length": meta.get("text_length"),
                    "content_preview": doc.page_content[:300],
                })

            result = {
                "id": item["id"],
                "discipline": item.get("discipline"),
                "question": question,
                "answer": answer,
                "retrieved": retrieved,
                "latency_sec": elapsed,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "top_k": TOP_K,
                "system_name": "System RAG with structured chunks and citation anchors",
                "model": MODEL_NAME,
                "vector_store": "Chroma",
                "collection_name": "system_rag",
                "adaptive_chunking": True,
                "metadata_enhanced": True,
                "citation_anchor_enabled": True,
                "rerank": False,
                "context_compression": False,
                "dynamic_top_k": False,
                "lora": False,
                "response_mode": response_mode,
            }

            out.write(json.dumps(result, ensure_ascii=False) + "\n")

            preview = sanitize_for_console(answer[:160], sys.stdout.encoding)
            print(f"Answer preview: {preview}")
            print(f"Latency: {elapsed:.2f}s | Tokens: {total_tokens}")

    print(f"\nSystem RAG results saved to: {output_path}")


if __name__ == "__main__":
    main()
