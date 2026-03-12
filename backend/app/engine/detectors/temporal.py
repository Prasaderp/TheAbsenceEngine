from __future__ import annotations
from pydantic import BaseModel
from app.engine.detectors.base import BaseDetector, DetectionContext, AbsenceCandidate
from app.engine.llm.prompts import TEMPORAL_EXTRACT


class _TemporalGap(BaseModel):
    description: str
    severity: float
    reasoning: str


class _TemporalResult(BaseModel):
    gaps: list[_TemporalGap]


class TemporalDetector(BaseDetector):
    async def detect(self, ctx: DetectionContext) -> list[AbsenceCandidate]:
        temporal_hints = ctx.ontology.temporal_considerations if ctx.ontology else []
        prompt = TEMPORAL_EXTRACT.format(
            text=ctx.document.text[:12000],
            domain=ctx.domain,
        )

        try:
            result = await ctx.llm.generate_structured(prompt, _TemporalResult)
        except Exception:
            return []

        candidates: list[AbsenceCandidate] = []
        for gap in result.gaps[:8]:
            sev = max(0.0, min(1.0, gap.severity))
            candidates.append(
                AbsenceCandidate(
                    title=f"Temporal gap: {gap.description[:80]}",
                    description=gap.description,
                    reasoning=gap.reasoning,
                    confidence=round(sev * 0.85, 3),
                    risk_score=round(sev * 0.8, 3),
                    absence_type="temporal_gap",
                    category="temporal",
                    evidence=[{"type": "temporal_analysis", "detail": gap.reasoning}],
                )
            )

        return candidates
