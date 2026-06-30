import json
import time
from pathlib import Path

import torch
from transformers import AutoTokenizer

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


PROJECT_ROOT = Path("/root/autodl-tmp/kd_agent_pipeline")

EVAL_PATH = PROJECT_ROOT / "data" / "eval" / "baseline_smoke_questions.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "baseline" / "baseline_results.jsonl"
PERSIST_DIR = str(PROJECT_ROOT / "data" / "indexes" / "chroma_baseline")

MODEL_NAME = "qwen-8b-instruct-baseline"
TOP_K = 5

BASELINE_PROMPT = """你是一个基于资料的问答助手。
请只根据给定资料回答问题。
如果资料中没有答案，请回答“未找到参考资料”。

问题：
{question}

资料：
{context}

请给出答案：
"""


def load_eval_questions(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def format_docs(docs):
    parts = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source_file", "")
        page = doc.metadata.get("page", "")
        discipline = doc.metadata.get("discipline", "")
        content = doc.page_content

        parts.append(
            f"[{i}] 来源文件: {source}, 页码: {page}, 学科: {discipline}\n{content}"
        )

    return "\n\n".join(parts)


def safe_count_tokens(text: str, tokenizer):
    try:
        return len(tokenizer.encode(text))
    except Exception:
        return int(len(text) / 1.5)


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

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
        collection_name="baseline_rag",
    )

    retriever = vectordb.as_retriever(search_kwargs={"k": TOP_K})

    llm = ChatOllama(
        model=MODEL_NAME,
        temperature=0,
        num_ctx=4096,
    )

    prompt = ChatPromptTemplate.from_template(BASELINE_PROMPT)

    with OUTPUT_PATH.open("w", encoding="utf-8") as out:
        for item in load_eval_questions(EVAL_PATH):
            question = item["question"]
            print(f"\nRunning question: {item['id']}")

            start = time.perf_counter()

            docs = retriever.invoke(question)
            context = format_docs(docs)

            prompt_text = BASELINE_PROMPT.format(
                question=question,
                context=context,
            )

            messages = prompt.invoke({
                "question": question,
                "context": context,
            })

            response = llm.invoke(messages)
            answer = response.content

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
                retrieved.append({
                    "source_file": doc.metadata.get("source_file"),
                    "page": doc.metadata.get("page"),
                    "discipline": doc.metadata.get("discipline"),
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
                "baseline_name": "LangChain + 标准 RAG + Qwen-8B-Instruct",
                "model": MODEL_NAME,
                "vector_store": "Chroma",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "adaptive_chunking": False,
                "rerank": False,
                "context_compression": False,
                "dynamic_top_k": False,
                "lora": False,
            }

            out.write(json.dumps(result, ensure_ascii=False) + "\n")

            print(f"Answer preview: {answer[:120]}")
            print(f"Latency: {elapsed:.2f}s | Tokens: {total_tokens}")

    print(f"\nBaseline results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
