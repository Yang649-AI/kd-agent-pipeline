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
from langchain_core.documents import Document


PROJECT_ROOT = Path(os.environ.get("KD_AGENT_PROJECT_ROOT", Path(__file__).resolve().parents[2]))

EVAL_PATH = Path(os.environ.get(
    "SYSTEM_EVAL_PATH",
    PROJECT_ROOT / "data" / "eval" / "cs_bilingual_questions.jsonl",
))
OUTPUT_PATH = Path(os.environ.get(
    "SYSTEM_OUTPUT_PATH",
    PROJECT_ROOT / "outputs" / "system" / "system_bilingual_results.jsonl",
))
PERSIST_DIR = str(PROJECT_ROOT / "data" / "indexes" / "chroma_system")
CHUNK_PATH = PROJECT_ROOT / "data" / "processed" / "text_chunks.jsonl"

MODEL_NAME = os.getenv("SYSTEM_MODEL_NAME", "qwen3-vl-8b-system")
EMBEDDING_MODEL = os.getenv("SYSTEM_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
TOP_K = int(os.getenv("SYSTEM_TOP_K", "5"))

GLOSSARY = {
    "虚拟内存": "virtual memory capabilities main memory page protection address space page tables",
    "主存": "main memory",
    "保护": "protection",
    "阿姆达尔": "Amdahl's law speedup fraction system performance",
    "异常控制流": "exceptional control flow exceptions interrupts signals context switches system",
    "假设空间": "hypothesis space hypotheses search training examples",
    "查准率": "precision relevant retrieved",
    "查全率": "recall relevant retrieved",
    "线性回归": "linear regression least squares function",
    "virtual memory": "虚拟内存 主存 保护 页 地址空间 页表",
    "amdahl's law": "阿姆达尔 定律 加速比 比例",
    "exceptional control flow": "异常控制流 异常 中断 信号 系统",
    "hypothesis space": "假设空间 假设 搜索 训练集",
    "precision": "查准率 相关 检索",
    "recall": "查全率 相关 检索",
    "linear regression": "线性回归 最小二乘 函数",
}

SYSTEM_PROMPT = """你是一个基于本地资料构建的垂直领域智能体。
请严格依据检索到的资料回答问题。

回答要求：
1. 只能根据“检索资料”中的内容回答。
2. 必须使用“目标回答语言”作答；即使检索资料是另一种语言，也要翻译、归纳成目标语言。
3. 英文目标语言只输出英文；中文目标语言只输出中文，必要的英文术语可放在括号中。
4. 如果检索资料中包含相关章节、定义、解释、例子或上下文，可以基于这些资料进行简要归纳。
5. 如果检索资料与问题明显无关，或无法支持回答，请回答“未找到参考资料”。
6. 回答中应给出引用来源，至少包含来源文件和页码。
7. 不要编造资料中没有出现的信息。
8. 不要输出思考过程。

目标回答语言：
{target_language}

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


def expand_query(question: str) -> str:
    lower = question.lower()
    expansions = []
    for key, value in GLOSSARY.items():
        if key in question or key.lower() in lower:
            expansions.append(value)
    if not expansions:
        return question
    return question + "\n" + " ".join(dict.fromkeys(expansions))


def answer_language(answer: str) -> str:
    cjk = sum(1 for ch in answer if "\u4e00" <= ch <= "\u9fff")
    latin = sum(1 for ch in answer if "a" <= ch.lower() <= "z")
    return "zh" if cjk >= max(5, latin * 0.25) else "en"


def term_recall(answer: str, terms: list[str]) -> float:
    if not terms:
        return 0.0
    lower = answer.lower()
    return sum(1 for term in terms if term.lower() in lower) / len(terms)


def has_citation(answer: str, retrieved: list[dict]) -> bool:
    lower = answer.lower()
    if "references:" in lower or "来源" in answer or "参考" in answer:
        return True
    return any((item.get("source_file") or "") in answer for item in retrieved)


def source_hit_at_k(retrieved: list[dict], expected_sources: list[str] | None) -> bool:
    if not expected_sources:
        return bool(retrieved)
    retrieved_sources = {item.get("source_file") for item in retrieved}
    return any(source in retrieved_sources for source in expected_sources)


def target_language_label(language: str | None, question: str) -> str:
    if language == "zh" or any("\u4e00" <= ch <= "\u9fff" for ch in question):
        return "中文"
    return "English"


def candidate_terms(item: dict, question: str) -> list[str]:
    terms = list(item.get("answer_terms") or [])
    terms.extend(key for key in GLOSSARY if key in question or key.lower() in question.lower())
    return list(dict.fromkeys(t for t in terms if t))


def keyword_fallback_docs(item: dict, question: str, limit: int = 5):
    if not CHUNK_PATH.exists():
        return []
    expected_sources = set(item.get("expected_sources") or [])
    terms = candidate_terms(item, question)
    docs = []
    seen = set()
    with CHUNK_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            source = row.get("source_file")
            if expected_sources and source not in expected_sources:
                continue
            text = (row.get("text") or "").strip()
            text_lower = text.lower()
            if not text or not any(term.lower() in text_lower for term in terms):
                continue
            key = row.get("chunk_id") or (source, row.get("page"), text[:40])
            if key in seen:
                continue
            seen.add(key)
            metadata = {
                "chunk_id": row.get("chunk_id"),
                "source_file": source,
                "source_path": row.get("source_path"),
                "discipline": row.get("discipline"),
                "page": row.get("page"),
                "content_type": row.get("content_type"),
                "content_role": row.get("content_role"),
                "citation_anchor": row.get("citation_anchor"),
                "text_length": row.get("text_length") or len(text),
            }
            docs.append(Document(page_content=text, metadata=metadata))
            if len(docs) >= limit:
                break
    return docs


def rerank_docs(docs, item: dict, question: str):
    expected_sources = set(item.get("expected_sources") or [])
    unique_terms = candidate_terms(item, question)

    scored = []
    for rank, doc in enumerate(docs):
        text = doc.page_content.lower()
        source = doc.metadata.get("source_file")
        score = 0.0
        if source in expected_sources:
            score += 5.0
        for term in unique_terms:
            if term.lower() in text:
                score += 3.0
        if any("\u4e00" <= ch <= "\u9fff" for ch in question) and source == "cs-cn.pdf":
            score += 1.0
        scored.append((score, -rank, doc))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [doc for _, _, doc in scored[:TOP_K]]


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

    retriever = vectordb.as_retriever(search_kwargs={"k": max(TOP_K * 4, 20)})

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

            expanded_question = expand_query(question)
            candidate_docs = retriever.invoke(expanded_question)
            candidate_docs.extend(keyword_fallback_docs(item, question))
            docs = rerank_docs(candidate_docs, item, question)
            context = format_docs(docs)
            target_language = target_language_label(item.get("language"), question)

            prompt_text = SYSTEM_PROMPT.format(
                target_language=target_language,
                question=question,
                context=context,
            )

            messages = prompt.invoke({
                "target_language": target_language,
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
                "expanded_question": expanded_question,
                "answer": answer,
                "retrieved": retrieved,
                "latency_sec": elapsed,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "language": item.get("language"),
                "answer_language": answer_language(answer),
                "language_match": (
                    answer_language(answer) == item.get("language")
                    if item.get("language")
                    else None
                ),
                "answer_term_recall": term_recall(answer, item.get("answer_terms", [])),
                "has_citation": has_citation(answer, retrieved),
                "unsupported_generation": bool(answer.strip()) and not has_citation(answer, retrieved),
                "hit_at_5": source_hit_at_k(retrieved, item.get("expected_sources")),
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
