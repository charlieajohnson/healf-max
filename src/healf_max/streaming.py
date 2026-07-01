from __future__ import annotations

from collections.abc import Iterator


def chunk_text(text: str, *, size: int = 36) -> Iterator[str]:
    words = text.split(" ")
    chunk: list[str] = []
    length = 0
    for word in words:
        chunk.append(word)
        length += len(word) + 1
        if length >= size:
            yield " ".join(chunk) + " "
            chunk = []
            length = 0
    if chunk:
        yield " ".join(chunk)
