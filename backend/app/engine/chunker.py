from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    text: str
    char_start: int
    char_end: int


def chunk_text(
    text: str,
    max_chars: int = 6000,
    overlap_chars: int = 800,
) -> list[Chunk]:
    if not text.strip():
        return []

    chunks: list[Chunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + max_chars, len(text))

        if end < len(text):
            # prefer paragraph break
            pb = text.rfind("\n\n", start, end)
            if pb > start + overlap_chars:
                end = pb + 2
            else:
                sb = text.rfind("\n", start + overlap_chars, end)
                if sb > start + overlap_chars:
                    end = sb + 1

        chunks.append(Chunk(index=idx, text=text[start:end], char_start=start, char_end=end))
        idx += 1
        start = end - overlap_chars if end < len(text) else end

    return chunks
