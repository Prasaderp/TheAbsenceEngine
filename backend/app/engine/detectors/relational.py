from __future__ import annotations
from pydantic import BaseModel
from app.engine.detectors.base import BaseDetector, DetectionContext, AbsenceCandidate
from app.engine.llm.prompts import RELATIONAL_EXTRACT

_PRIMARY_DOMAINS = {"interpersonal", "strategy", "product"}
_PRIMARY_DISCOUNT = 0.85
_SECONDARY_DISCOUNT = 0.60
_MAX_GAPS = 8


class _RelationalGap(BaseModel):
    entity: str
    missing_dimension: str
    description: str
    severity: float


class _RelationalResult(BaseModel):
    gaps: list[_RelationalGap]


class RelationalDetector(BaseDetector):
    """Beta detector — confidence discounted for all domains, more for non-primary."""

    async def detect(self, ctx: DetectionContext) -> list[AbsenceCandidate]:
        discount = _PRIMARY_DISCOUNT if ctx.domain in _PRIMARY_DOMAINS else _SECONDARY_DISCOUNT
        prompt = RELATIONAL_EXTRACT.format(text=ctx.document.text[:12000])

        try:
            result = await ctx.llm.generate_structured(prompt, _RelationalResult)
        except Exception:
            return []

        candidates: list[AbsenceCandidate] = []
        for gap in result.gaps[:_MAX_GAPS]:
            sev = max(0.0, min(1.0, gap.severity)) * discount
            candidates.append(
                AbsenceCandidate(
                    title=f"Relational gap: {gap.entity} — {gap.missing_dimension}",
                    description=gap.description,
                    reasoning=f"Entity '{gap.entity}' lacks '{gap.missing_dimension}' framing. (beta detector, discount={discount})",
                    confidence=round(sev, 3),
                    risk_score=round(sev * 0.75, 3),
                    absence_type="emotional_relational",
                    category="relational",
                    evidence=[{"type": "relational_analysis", "detail": gap.description}],
                )
            )

        return candidates
