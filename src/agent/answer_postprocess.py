import re


THINK_LINE_RE = re.compile(r"^\s*/?think\s*$|^\s*</?think>\s*$", re.IGNORECASE)
THINK_BLOCK_RE = re.compile(r"<think\b[^>]*>.*?</think>", re.IGNORECASE | re.DOTALL)


def clean_ollama_answer(answer: str) -> str:
    """Remove Qwen thinking artifacts without changing the answer format."""
    cleaned = THINK_BLOCK_RE.sub("", answer)
    lines = [
        line.rstrip()
        for line in cleaned.splitlines()
        if not THINK_LINE_RE.match(line)
    ]
    cleaned = "\n".join(lines).strip()

    answer_positions = [match.start() for match in re.finditer(r"(?m)^Answer:", cleaned)]
    if len(answer_positions) > 1:
        cleaned = cleaned[answer_positions[-1]:].strip()

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
