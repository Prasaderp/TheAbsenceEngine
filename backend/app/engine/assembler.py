from __future__ import annotations
from app.engine.detectors.base import AbsenceCandidate
from app.engine.embedder import cosine_similarity
from app.engine.llm.gateway import LLMGateway
from app.engine.llm.prompts import SUGGEST_COMPLETION
from app.shared.logger import get_logger

log = get_logger(__name__)

_DEDUP_THRESHOLD = 0.85
_MAX_ITEMS = 25
_SUGGESTION_COUNT = 5

_TYPE_SEVERITY: dict[str, float] = {
    "coverage_gap": 0.85,
    "logical_implication": 0.80,
    "stakeholder_gap": 0.75,
    "temporal_gap": 0.70,
    "structural_gap": 0.65,
    "emotional_relational": 0.50,
}


def _compute_risk(candidate: AbsenceCandidate) -> float:
    """Risk = (raw_risk × 0.35) + (confidence × 0.35) + (type_severity × 0.30)"""
    type_sev = _TYPE_SEVERITY.get(candidate.absence_type, 0.5)
    raw = (candidate.risk_score * 0.35) + (candidate.confidence * 0.35) + (type_sev * 0.30)
    return round(max(0.0, min(1.0, raw)), 3)


def _deduplicate(
    candidates: list[AbsenceCandidate],
    embeddings: dict[int, list[float]],
) -> list[AbsenceCandidate]:
    kept: list[int] = []
    for i in range(len(candidates)):
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
    deduped.sort(key=lambda c: _compute_risk(c), reverse=True)
    deduped = deduped[:_MAX_ITEMS]

    for item in deduped[:_SUGGESTION_COUNT]:
        try:
            prompt = SUGGEST_COMPLETION.format(
                excerpt=document_text[:2000],
                title=item.title,
                description=item.description,
            )
            resp = await llm.generate(prompt, max_tokens=512)
            item.suggested_completion = resp.text.strip()
        except Exception as exc:
            log.warning("suggestion generation failed", extra={"title": item.title, "error": str(exc)})

    risks = [_compute_risk(c) for c in deduped]
    overall_risk = round(sum(risks) / max(len(risks), 1), 3)

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
                "risk_score": _compute_risk(c),
                "evidence": c.evidence,
                "suggested_completion": c.suggested_completion,
            }
            for c in deduped
        ],
    }
