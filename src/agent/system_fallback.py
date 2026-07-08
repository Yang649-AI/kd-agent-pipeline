import re


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def build_extractive_fallback_answer(docs) -> str:
    if not docs:
        return "未找到参考资料"

    top_doc = docs[0]
    sentences = _split_sentences(top_doc.page_content)
    evidence = sentences[:3] if sentences else [top_doc.page_content.strip()]
    evidence = [item for item in evidence if item]
    if not evidence:
        return "未找到参考资料"

    metadata = top_doc.metadata
    citation = metadata.get("citation_anchor") or (
        f"{metadata.get('source_file', '')}#page={metadata.get('page', '')}"
    )

    return (
        "Answer:\n"
        + " ".join(evidence)
        + "\nReferences:\n"
        + f"- {citation}"
    )
