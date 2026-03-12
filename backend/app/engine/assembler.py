from __future__ import annotations
import math
from app.engine.detectors.base import AbsenceCandidate
from app.engine.embedder import cosine_similarity
from app.engine.llm.gateway import LLMGateway
from app.engine.llm.prompts import SUGGEST_COMPLETION

_DEDUP_THRESHOLD = 0.85
_MAX_ITEMS = 25


def _risk(candidate: AbsenceCandidate) -> float:
    return round(
        (candidate.risk_score * 0.4) + (candidate.confidence * 0.4) + (0.2 * (1.0 if candidate.absence_type == "coverage_gap" else 0.6)),
        3,
    )


def _deduplicate(
    candidates: list[AbsenceCandidate],
    embeddings: dict[int, list[float]],
) -> list[AbsenceCandidate]:
    kept: list[int] = []
    for i, _ in enumerate(candidates):
        merge = False
        for j in kept:
            if i in embeddings and j in embeddings:
                sim = cosine_similarity(embeddings[i], embeddings[j])
                if sim >= _DEDUP_THRESHOLD:
                    if candidates[i].confidence > candidates[j].confidence:
                        kept[kept.index(j)] = i
                    merge = True
                    break
        if not merge:
            kept.append(i)
    return [candidates[k] for k in kept]


async def assemble(
    candidates: list[AbsenceCandidate],
    document_text: str,
    llm: LLMGateway,
) -> dict:
    if not candidates:
        return {"summary": "No significant absences detected.", "overall_risk_score": 0.0, "items": []}

    title_texts = [c.title for c in candidates]
    try:
        vectors = await llm.embed(title_texts)
        emb_map = {i: v for i, v in enumerate(vectors)}
    except Exception:
        emb_map = {}

    deduped = _deduplicate(candidates, emb_map)
    deduped.sort(key=lambda c: _risk(c), reverse=True)
    deduped = deduped[:_MAX_ITEMS]

    for item in deduped[:5]:
        try:
            prompt = SUGGEST_COMPLETION.format(
                excerpt=document_text[:2000],
                title=item.title,
                description=item.description,
            )
            resp = await llm.generate(prompt, max_tokens=512)
            item.suggested_completion = resp.text.strip()
        except Exception:
            pass

    overall_risk = round(
        sum(_risk(c) * c.confidence for c in deduped) / max(len(deduped), 1),
        3,
    )

    item_count = len(deduped)
    summary = (
        f"Found {item_count} significant absence{'s' if item_count != 1 else ''} "
        f"with an overall risk score of {overall_risk:.2f}."
    )

    return {
        "summary": summary,
        "overall_risk_score": overall_risk,
        "items": [
            {
                "title": c.title,
                "category": c.category,
                "absence_type": c.absence_type,
                "description": c.description,
                "reasoning": c.reasoning,
                "confidence": c.confidence,
                "risk_score": _risk(c),
                "evidence": c.evidence,
                "suggested_completion": c.suggested_completion,
            }
            for c in deduped
        ],
    }
