import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from langchain_core.documents import Document


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.answer_postprocess import clean_ollama_answer
from agent.run_system_rag import (
    MODEL_NAME,
    PERSIST_DIR,
    SYSTEM_PROMPT,
    TOP_K,
    format_docs,
)
from agent.system_fallback import build_extractive_fallback_answer
from common.console_text import sanitize_for_console


ACC_24E3_HARDWARE_MANUAL = "_info_OMRON_Delta_Tau_ACC_24E3_Manual_2024314151533.pdf"


def parse_question(parts: list[str]) -> str:
    question = " ".join(part.strip() for part in parts if part.strip()).strip()
    if not question:
        raise ValueError("Question cannot be empty.")
    return question


def configure_offline_huggingface(env: dict | None = None) -> None:
    env = os.environ if env is None else env
    env.setdefault("HF_HUB_OFFLINE", "1")
    env.setdefault("TRANSFORMERS_OFFLINE", "1")
    env.setdefault("HF_DATASETS_OFFLINE", "1")
    env.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def build_embedding_model_kwargs(device: str) -> dict:
    return {
        "device": device,
        "local_files_only": True,
    }


def extract_query_symbols(question: str) -> list[str]:
    pattern = re.compile(
        r"\b[A-Za-z][A-Za-z0-9_]*(?:\[[A-Za-z0-9_]+\])?(?:\.[A-Za-z][A-Za-z0-9_]*)+\b"
    )
    return _unique_preserve_order(pattern.findall(question))


def extract_command_patterns(question: str) -> list[str]:
    command_hits: list[tuple[int, str]] = []

    brace_command_pattern = re.compile(
        r"\b[A-Za-z]\{[^}]+\}\s*(?:->|=\s*\{[^}]+\}|=\s*[\w.\-]+)?"
    )
    for match in brace_command_pattern.finditer(question):
        command = re.sub(r"\s+", "", match.group(0))
        if "->" in command or "=" in command:
            command_hits.append((match.start(), command))

    question_lower = question.lower()
    for phrase in ["undefine all", "vers"]:
        index = question_lower.find(phrase)
        if index >= 0:
            command_hits.append((index, phrase))

    v_match = re.search(r"\bv\s+command\b|\bcommand\s+v\b", question_lower)
    if v_match:
        command_hits.append((v_match.start(), "v"))

    return _unique_preserve_order([command for _, command in sorted(command_hits)])


def lexical_symbol_score(question: str, doc: Document) -> int:
    symbols = extract_query_symbols(question)
    if not symbols:
        return 0

    text_lower = doc.page_content.lower()
    score = 0

    for symbol in symbols:
        symbol_lower = symbol.lower()
        occurrences = text_lower.count(symbol_lower)
        if occurrences:
            score += 6 + min(occurrences, 4)

    if score:
        for term in ["description", "purpose", "used", "controls", "providing"]:
            if term in text_lower:
                score += 1

    return score


def _normalize_command_text(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"\s*(->|=)\s*", r"\1", normalized)
    return re.sub(r"\s+", " ", normalized)


def _command_occurrences(command: str, normalized_text: str) -> int:
    if command in {"v", "vers"}:
        return len(
            re.findall(
                rf"(?<![A-Za-z0-9_]){re.escape(command)}(?![A-Za-z0-9_])",
                normalized_text,
            )
        )

    if re.fullmatch(r"[a-z]+(?:\s+[a-z]+)+", command):
        return len(
            re.findall(
                rf"(?<![A-Za-z0-9_]){re.escape(command)}(?![A-Za-z0-9_])",
                normalized_text,
            )
        )

    return normalized_text.count(command)


def lexical_command_score(question: str, doc: Document) -> int:
    commands = extract_command_patterns(question)
    if not commands:
        return 0

    text_lower = doc.page_content.lower()
    normalized_text = _normalize_command_text(doc.page_content)
    score = 0

    for command in commands:
        normalized_command = _normalize_command_text(command)
        occurrences = _command_occurrences(normalized_command, normalized_text)
        if occurrences:
            score += 7 + min(occurrences, 5)

            spec_patterns = [
                f"{normalized_command} function:",
                f"syntax:{normalized_command}",
                f"syntax: {normalized_command}",
                f"syntax: the {normalized_command} command",
                f"the {normalized_command} command causes",
            ]
            for pattern in spec_patterns:
                if pattern in normalized_text:
                    score += 4
                    break

            if "power pmac on-line command specification" in normalized_text:
                score += 2

    if score:
        for term in ["command", "reports", "report", "returns", "return", "function", "syntax"]:
            if term in text_lower:
                score += 1

    return score


def is_acc_24e3_query(question: str) -> bool:
    return bool(re.search(r"\bacc[-\s]?24e3\b", question.lower()))


def lexical_acc_hardware_score(question: str, doc: Document) -> int:
    if not is_acc_24e3_query(question):
        return 0

    question_lower = question.lower()
    text_lower = doc.page_content.lower()
    source_file = str(doc.metadata.get("source_file") or "").lower()
    score = 0

    if source_file == ACC_24E3_HARDWARE_MANUAL.lower():
        score += 8
    elif "acc_24e3" in source_file or "acc-24e3" in source_file:
        score += 5

    if "acc-24e3" in text_lower or "acc 24e3" in text_lower:
        score += 4
    elif "acc24e3" in text_lower:
        score += 1

    topic_terms = [
        (
            ["document number"],
            ["document number", "document no", "manual number", "o015", "acc-24e3"],
            4,
        ),
        (
            ["operating temperature", "temperature range", "environmental"],
            ["operating temperature", "temperature", "environmental", "humidity"],
            4,
        ),
        (
            ["channel", "channels", "axis interface"],
            ["channel", "channels", "axis interface", "axis-interface"],
            4,
        ),
        (
            ["compatible", "turbo pmac", "umac cpu"],
            ["compatible", "turbo pmac", "umac cpu", "power pmac"],
            4,
        ),
        (
            ["amplifier", "amplifiers", "drive", "drives"],
            ["amplifier", "amplifiers", "drive", "drives", "command signal"],
            4,
        ),
        (
            ["position feedback", "feedback"],
            ["position feedback", "encoder", "resolver", "sinusoidal", "hall"],
            4,
        ),
        (
            ["used for", "purpose", "what is the acc"],
            ["axis interface", "interface board", "channels", "servo", "feedback"],
            3,
        ),
    ]
    for query_terms, doc_terms, bonus in topic_terms:
        if any(term in question_lower for term in query_terms) and any(
            term in text_lower for term in doc_terms
        ):
            score += bonus

    if "table of contents" in text_lower:
        score -= 5

    if source_file != ACC_24E3_HARDWARE_MANUAL.lower() and "acc24e3[" in text_lower:
        score -= 2

    return max(score, 0)


def lexical_contact_score(question: str, doc: Document) -> int:
    question_lower = question.lower()
    text_lower = doc.page_content.lower()
    score = 0

    if "email" in question_lower or "e-mail" in question_lower:
        if re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", doc.page_content):
            score += 5
        if "email" in text_lower or "e-mail" in text_lower:
            score += 2

    if "phone" in question_lower or "telephone" in question_lower:
        if re.search(r"\b(?:\+?\d[\d\-\s().]{6,}\d)\b", doc.page_content):
            score += 5
        if "phone" in text_lower or "telephone" in text_lower:
            score += 2

    if "technical support" in question_lower:
        if "technical support" in text_lower:
            score += 3
        elif "support" in text_lower:
            score += 1

    for term in ["support", "omron", "delta tau", "pmac"]:
        if term in question_lower and term in text_lower:
            score += 1

    return score


def _doc_key(doc: Document) -> str:
    meta = doc.metadata
    return str(meta.get("chunk_id") or meta.get("citation_anchor") or id(doc))


def merge_retrieved_docs(
    vector_docs: list[Document],
    lexical_docs: list[tuple[int, Document]],
    limit: int,
) -> list[Document]:
    merged: list[Document] = []
    seen: set[str] = set()

    for _, doc in sorted(lexical_docs, key=lambda item: item[0], reverse=True):
        key = _doc_key(doc)
        if key not in seen:
            merged.append(doc)
            seen.add(key)
        if len(merged) >= limit:
            return merged

    for doc in vector_docs:
        key = _doc_key(doc)
        if key not in seen:
            merged.append(doc)
            seen.add(key)
        if len(merged) >= limit:
            break

    return merged


def _citation_for_doc(doc: Document) -> str:
    meta = doc.metadata
    return str(
        meta.get("citation_anchor")
        or f"{meta.get('source_file')}#page={meta.get('page')}"
    )


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        normalized = value.strip().rstrip(".,;)")
        key = normalized.lower()
        if normalized and key not in seen:
            unique.append(normalized)
            seen.add(key)
    return unique


def extract_direct_contact_answer(question: str, docs: list[Document]) -> str | None:
    question_lower = question.lower()
    wants_email = "email" in question_lower or "e-mail" in question_lower
    wants_phone = "phone" in question_lower or "telephone" in question_lower

    if not wants_email and not wants_phone:
        return None

    email_pattern = re.compile(r"[\w.\-+]+@[\w.\-]+\.\w+")
    phone_pattern = re.compile(
        r"(?:\+?\d[\d\-\s().]{6,}\d)"
    )

    for doc in docs:
        text = doc.page_content
        citation = _citation_for_doc(doc)

        if wants_email:
            emails = _unique_preserve_order(email_pattern.findall(text))
            if emails:
                return (
                    "Answer:\n"
                    + " and ".join(emails)
                    + "\nReferences:\n"
                    + f"- {citation}"
                )

        if wants_phone:
            phones = _unique_preserve_order(phone_pattern.findall(text))
            if phones:
                return (
                    "Answer:\n"
                    + " and ".join(phones)
                    + "\nReferences:\n"
                    + f"- {citation}"
                )

    return None


def find_lexical_boost_docs(vectordb, question: str, limit: int) -> list[tuple[int, Document]]:
    question_lower = question.lower()
    contact_query = any(
        term in question_lower
        for term in ["email", "e-mail", "phone", "telephone", "technical support"]
    )
    symbol_query = bool(extract_query_symbols(question))
    command_query = bool(extract_command_patterns(question))
    acc_query = is_acc_24e3_query(question)

    if not contact_query and not symbol_query and not command_query and not acc_query:
        return []

    data = vectordb.get(include=["documents", "metadatas"], limit=20000)
    documents = data.get("documents") or []
    metadatas = data.get("metadatas") or []

    scored: list[tuple[int, Document]] = []
    for text, metadata in zip(documents, metadatas):
        doc = Document(page_content=text or "", metadata=metadata or {})
        score = (
            lexical_contact_score(question, doc)
            + lexical_symbol_score(question, doc)
            + lexical_command_score(question, doc)
            + lexical_acc_hardware_score(question, doc)
        )
        if score > 0:
            scored.append((score, doc))

    return sorted(scored, key=lambda item: item[0], reverse=True)[:limit]


def _retrieved_records(docs) -> list[dict]:
    records = []
    for doc in docs:
        meta = doc.metadata
        records.append({
            "chunk_id": meta.get("chunk_id"),
            "source_file": meta.get("source_file"),
            "page": meta.get("page"),
            "discipline": meta.get("discipline"),
            "content_type": meta.get("content_type"),
            "citation_anchor": meta.get("citation_anchor"),
            "text_length": meta.get("text_length"),
            "content_preview": doc.page_content[:300],
        })
    return records


def build_result_record(
    question: str,
    answer: str,
    docs,
    latency_sec: float,
    input_tokens: int,
    output_tokens: int,
    response_mode: str,
) -> dict:
    return {
        "id": "manual",
        "discipline": "power_pmac",
        "question": question,
        "answer": answer,
        "retrieved": _retrieved_records(docs),
        "latency_sec": latency_sec,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "top_k": TOP_K,
        "system_name": "System RAG single-question mode",
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


def rough_token_count(text: str) -> int:
    return int(len(text) / 1.5)


def answer_question_once(question: str) -> dict:
    configure_offline_huggingface()

    import torch
    from langchain_chroma import Chroma
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_ollama import ChatOllama

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Embedding device: {device}")

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-zh-v1.5",
        model_kwargs=build_embedding_model_kwargs(device),
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

    start = time.perf_counter()
    vector_docs = retriever.invoke(question)
    lexical_docs = find_lexical_boost_docs(vectordb, question, limit=TOP_K)
    docs = merge_retrieved_docs(vector_docs, lexical_docs, limit=TOP_K)
    context = format_docs(docs)
    prompt_text = SYSTEM_PROMPT.format(question=question, context=context)
    messages = prompt.invoke({"question": question, "context": context})

    direct_answer = extract_direct_contact_answer(question, docs)
    if direct_answer:
        answer = direct_answer
        response_mode = "direct_extract"
    else:
        try:
            response = llm.invoke(messages)
            answer = clean_ollama_answer(response.content)
            response_mode = "ollama"
        except Exception as exc:
            print(
                "Ollama invocation failed, using extractive fallback. "
                f"Reason: {exc!r}"
            )
            answer = build_extractive_fallback_answer(docs)
            response_mode = "extractive_fallback"

    elapsed = time.perf_counter() - start
    return build_result_record(
        question=question,
        answer=answer,
        docs=docs,
        latency_sec=elapsed,
        input_tokens=rough_token_count(prompt_text),
        output_tokens=rough_token_count(answer),
        response_mode=response_mode,
    )


def format_human_readable(result: dict) -> str:
    lines = [
        "Question:",
        result["question"],
        "",
        "Result:",
        result["answer"],
        "",
        "Retrieved references:",
    ]
    for idx, item in enumerate(result["retrieved"], start=1):
        citation = item.get("citation_anchor") or (
            f"{item.get('source_file')}#page={item.get('page')}"
        )
        lines.append(f"{idx}. {citation}")
    lines.extend([
        "",
        f"\nMode: {result['response_mode']} | "
        f"Latency: {result['latency_sec']:.2f}s | "
        f"Tokens: {result['total_tokens']}",
    ])
    return "\n".join(lines)


def print_human_readable(result: dict) -> None:
    text = format_human_readable(result)
    print(sanitize_for_console(text, sys.stdout.encoding))


def append_jsonl(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ask one question against the existing system RAG index."
    )
    parser.add_argument("question_parts", nargs="*", help="Question text.")
    parser.add_argument("--question", help="Question text.")
    parser.add_argument("--json", action="store_true", help="Print JSON result.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSONL file to append the result to.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_offline_huggingface()

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        question = args.question.strip() if args.question else parse_question(args.question_parts)
        if not question:
            raise ValueError("Question cannot be empty.")
    except ValueError as exc:
        parser.error(str(exc))

    result = answer_question_once(question)

    if args.output:
        append_jsonl(args.output, result)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human_readable(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
