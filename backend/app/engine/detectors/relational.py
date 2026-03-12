from __future__ import annotations
from pydantic import BaseModel
from app.engine.detectors.base import BaseDetector, DetectionContext, AbsenceCandidate
from app.engine.llm.prompts import RELATIONAL_EXTRACT

_CONFIDENCE_DISCOUNT = 0.8


class _RelationalGap(BaseModel):
    entity: str
    missing_dimension: str
    description: str
    severity: float


class _RelationalResult(BaseModel):
    gaps: list[_RelationalGap]


class RelationalDetector(BaseDetector):
    """Beta detector — confidence discounted 20%."""

    async def detect(self, ctx: DetectionContext) -> list[AbsenceCandidate]:
        if ctx.domain not in {"interpersonal", "strategy", "product"}:
            return []

        prompt = RELATIONAL_EXTRACT.format(text=ctx.document.text[:10000])

        try:
            result = await ctx.llm.generate_structured(prompt, _RelationalResult)
        except Exception:
            return []

        candidates: list[AbsenceCandidate] = []
        for gap in result.gaps[:6]:
            sev = max(0.0, min(1.0, gap.severity)) * _CONFIDENCE_DISCOUNT
            candidates.append(
                AbsenceCandidate(
                    title=f"Relational gap: {gap.entity} — {gap.missing_dimension}",
                    description=gap.description,
                    reasoning=f"Entity '{gap.entity}' lacks {gap.missing_dimension} framing. (beta detector, confidence discounted)",
                    confidence=round(sev, 3),
                    risk_score=round(sev * 0.7, 3),
                    absence_type="emotional_relational",
                    category="relational",
                    evidence=[{"type": "relational_analysis", "detail": gap.description}],
                )
            )

        return candidates
