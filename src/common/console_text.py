def sanitize_for_console(text: str, encoding: str | None) -> str:
    if not encoding:
        return text
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")
