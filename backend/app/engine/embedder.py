from __future__ import annotations
import math
from dataclasses import dataclass
from app.engine.chunker import Chunk
from app.engine.llm.gateway import LLMGateway


@dataclass
class EmbeddingChunk:
    chunk: Chunk
    embedding: list[float]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


async def embed_chunks(chunks: list[Chunk], llm: LLMGateway) -> list[EmbeddingChunk]:
    if not chunks:
        return []
    texts = [c.text for c in chunks]
    vectors = await llm.embed(texts)
    return [EmbeddingChunk(chunk=c, embedding=v) for c, v in zip(chunks, vectors)]


def semantic_search(
    query_embedding: list[float],
    corpus: list[EmbeddingChunk],
    top_k: int = 5,
) -> list[tuple[EmbeddingChunk, float]]:
    scored = [(ec, cosine_similarity(query_embedding, ec.embedding)) for ec in corpus]
    return sorted(scored, key=lambda x: x[1], reverse=True)[:top_k]
