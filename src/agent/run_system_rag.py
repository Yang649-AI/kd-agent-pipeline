import json
import os
import time
from pathlib import Path

import torch
from transformers import AutoTokenizer

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


PROJECT_ROOT = Path(os.environ.get("KD_AGENT_PROJECT_ROOT", Path(__file__).resolve().parents[2]))

EVAL_PATH = PROJECT_ROOT / "data" / "eval" / "baseline_smoke_questions.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "system" / "system_results.jsonl"
PERSIST_DIR = str(PROJECT_ROOT / "data" / "indexes" / "chroma_system")

MODEL_NAME = os.getenv("SYSTEM_MODEL_NAME", "qwen3-vl-8b-system")
EMBEDDING_MODEL = os.getenv("SYSTEM_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
TOP_K = 4

SYSTEM_PROMPT = """你是一个基于本地资料构建的垂直领域智能体。
请严格依据检索到的资料回答问题。

回答要求：
1. 只能根据“检索资料”中的内容回答。
2. 回答语言必须与问题语言保持一致：英文问题用英文回答，中文问题用中文回答。
3. 如果检索资料中包含相关章节、定义、解释、例子或上下文，可以基于这些资料进行简要归纳。
4. 如果检索资料与问题明显无关，或无法支持回答，请回答“未找到参考资料”。
5. 回答中应给出引用来源，至少包含来源文件和页码。
6. 不要编造资料中没有出现的信息。
7. 不要输出思考过程。

问题：
{question}

检索资料：
{context}

请按以下格式回答：
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
            f"来源文件: {source}\n"
            f"页码: {page}\n"
            f"引用锚点: {anchor}\n"
            f"知识块ID: {chunk_id}\n"
            f"内容类型: {content_type}\n"
            f"正文:\n{text}"
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
            os.getenv("SYSTEM_TOKENIZER_NAME", "Qwen/Qwen3-VL-8B-Instruct"),
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
        model_name=EMBEDDING_MODEL,
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

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    with OUTPUT_PATH.open("w", encoding="utf-8") as out:
        for item in load_eval_questions(EVAL_PATH):
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
            }

            out.write(json.dumps(result, ensure_ascii=False) + "\n")

            print(f"Answer preview: {answer[:160]}")
            print(f"Latency: {elapsed:.2f}s | Tokens: {total_tokens}")

    print(f"\nSystem RAG results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
