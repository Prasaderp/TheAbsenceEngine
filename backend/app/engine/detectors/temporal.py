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


_MAX_GAPS = 10


class TemporalDetector(BaseDetector):
    async def detect(self, ctx: DetectionContext) -> list[AbsenceCandidate]:
        temporal_hints = ctx.ontology.temporal_considerations if ctx.ontology else []
        hints_str = ", ".join(temporal_hints) if temporal_hints else "none specified"

        prompt = TEMPORAL_EXTRACT.format(
            text=ctx.document.text[:15000],
            domain=ctx.domain,
            temporal_hints=hints_str,
        )

        try:
            result = await ctx.llm.generate_structured(prompt, _TemporalResult)
        except Exception:
            return []

        candidates: list[AbsenceCandidate] = []
        for gap in result.gaps[:_MAX_GAPS]:
            sev = max(0.0, min(1.0, gap.severity))
            is_ontology_match = any(
                hint.lower() in gap.description.lower() or gap.description.lower() in hint.lower()
                for hint in temporal_hints
            )
            confidence_boost = 1.1 if is_ontology_match else 1.0
            confidence = round(min(0.95, sev * 0.85 * confidence_boost), 3)
            risk = round(min(0.95, sev * 0.80 * confidence_boost), 3)

            candidates.append(
                AbsenceCandidate(
                    title=f"Temporal gap: {gap.description[:80]}",
                    description=gap.description,
                    reasoning=gap.reasoning,
                    confidence=confidence,
                    risk_score=risk,
                    absence_type="temporal_gap",
                    category="temporal",
                    evidence=[
                        {"type": "temporal_analysis", "detail": gap.reasoning},
                        *([{"type": "ontology_match", "detail": "Matches domain temporal consideration"}] if is_ontology_match else []),
                    ],
                )
            )

        return candidates
