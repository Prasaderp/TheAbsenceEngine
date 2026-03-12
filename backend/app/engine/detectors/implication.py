from __future__ import annotations
from pydantic import BaseModel
from app.engine.detectors.base import BaseDetector, DetectionContext, AbsenceCandidate
from app.engine.embedder import semantic_search
from app.engine.llm.prompts import EXTRACT_ASSERTIONS, COVERAGE_VERIFY


class _Implication(BaseModel):
    topic: str
    description: str


class _Assertion(BaseModel):
    assertion: str
    section: str
    implications: list[_Implication]


class _AssertionList(BaseModel):
    assertions: list[_Assertion]


_ADDR_THRESHOLD = 0.6


class ImplicationDetector(BaseDetector):
    async def detect(self, ctx: DetectionContext) -> list[AbsenceCandidate]:
        if not ctx.embeddings:
            return []

        prompt = EXTRACT_ASSERTIONS.format(text=ctx.document.text[:12000])
        try:
            result = await ctx.llm.generate_structured(prompt, _AssertionList)
        except Exception:
            return []

        candidates: list[AbsenceCandidate] = []

        for assertion in result.assertions[:10]:
            for impl in assertion.implications[:3]:
                q_emb = await ctx.llm.embed([impl.description])
                top = semantic_search(q_emb[0], ctx.embeddings, top_k=3)
                best = top[0][1] if top else 0.0

                if best >= _ADDR_THRESHOLD:
                    continue

                candidates.append(
                    AbsenceCandidate(
                        title=f"Unaddressed implication: {impl.topic}",
                        description=impl.description,
                        reasoning=f"Assertion '{assertion.assertion[:100]}' implies this topic must be addressed, but no evidence found (similarity {best:.2f}).",
                        confidence=round((1 - best) * 0.85, 3),
                        risk_score=round((1 - best) * 0.75, 3),
                        absence_type="logical_implication",
                        category="logical_consistency",
                        evidence=[
                            {"type": "logical_implication", "detail": f"Assertion: {assertion.assertion[:200]}"},
                            {"type": "source_section", "detail": assertion.section},
                        ],
                    )
                )

        return candidates
