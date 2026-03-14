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


_ADDR_THRESHOLD = 0.60
_WEAK_THRESHOLD = 0.72
_MAX_ASSERTIONS = 15
_MAX_IMPLICATIONS = 5


class _VerifyResult(BaseModel):
    is_addressed: bool
    explanation: str
    confidence: float


class ImplicationDetector(BaseDetector):
    async def detect(self, ctx: DetectionContext) -> list[AbsenceCandidate]:
        prompt = EXTRACT_ASSERTIONS.format(text=ctx.document.text[:15000])
        try:
            result = await ctx.llm.generate_structured(prompt, _AssertionList)
        except Exception:
            return []

        candidates: list[AbsenceCandidate] = []

        for assertion in result.assertions[:_MAX_ASSERTIONS]:
            for impl in assertion.implications[:_MAX_IMPLICATIONS]:
                best_score = 0.0

                if ctx.embeddings:
                    try:
                        q_emb = await ctx.llm.embed([impl.description])
                        top = semantic_search(q_emb[0], ctx.embeddings, top_k=3)
                        best_score = top[0][1] if top else 0.0
                    except Exception:
                        pass

                if best_score >= _WEAK_THRESHOLD:
                    continue

                if best_score >= _ADDR_THRESHOLD:
                    try:
                        excerpt = ctx.document.text[:2000]
                        if ctx.embeddings:
                            q_emb = await ctx.llm.embed([impl.description])
                            top = semantic_search(q_emb[0], ctx.embeddings, top_k=2)
                            excerpt = "\n".join(h.chunk.text[:500] for h, _ in top) if top else excerpt
                        verify = await ctx.llm.generate_structured(
                            COVERAGE_VERIFY.format(topic=impl.description, excerpt=excerpt),
                            _VerifyResult,
                        )
                        if verify.is_addressed:
                            continue
                    except Exception:
                        continue

                confidence = round(max(0.2, (1.0 - best_score) * 0.85), 3)
                risk = round(max(0.15, (1.0 - best_score) * 0.75), 3)

                candidates.append(
                    AbsenceCandidate(
                        title=f"Unaddressed implication: {impl.topic}",
                        description=impl.description,
                        reasoning=f"Assertion '{assertion.assertion[:120]}' implies this topic must be addressed. Semantic match: {best_score:.2f}.",
                        confidence=confidence,
                        risk_score=risk,
                        absence_type="logical_implication",
                        category="logical_consistency",
                        evidence=[
                            {"type": "logical_implication", "detail": f"Source assertion: {assertion.assertion[:250]}"},
                            {"type": "source_section", "detail": assertion.section},
                        ],
                    )
                )

        return candidates
