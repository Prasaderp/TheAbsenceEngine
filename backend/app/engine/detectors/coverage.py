from __future__ import annotations
from pydantic import BaseModel
from app.engine.detectors.base import BaseDetector, DetectionContext, AbsenceCandidate
from app.engine.embedder import semantic_search
from app.engine.llm.prompts import COVERAGE_VERIFY

_GAP_THRESHOLD = 0.55


class _VerifyResult(BaseModel):
    is_addressed: bool
    explanation: str
    confidence: float


class CoverageDetector(BaseDetector):
    async def detect(self, ctx: DetectionContext) -> list[AbsenceCandidate]:
        if not ctx.ontology or not ctx.embeddings:
            return []

        candidates: list[AbsenceCandidate] = []

        for section in ctx.ontology.required_sections:
            query_emb = await ctx.llm.embed([section.description])
            top = semantic_search(query_emb[0], ctx.embeddings, top_k=3)
            best_score = top[0][1] if top else 0.0

            if best_score >= _GAP_THRESHOLD:
                continue

            excerpt = "\n".join(h.chunk.text[:400] for h, _ in top[:2]) if top else ctx.document.text[:800]
            prompt = COVERAGE_VERIFY.format(topic=section.description, excerpt=excerpt)

            try:
                result = await ctx.llm.generate_structured(prompt, _VerifyResult)
                if result.is_addressed:
                    continue
                confidence = result.confidence * (1 - best_score)
            except Exception:
                confidence = (1 - best_score) * 0.7

            candidates.append(
                AbsenceCandidate(
                    title=f"Missing: {section.name.replace('_', ' ').title()}",
                    description=section.description,
                    reasoning=f"Semantic similarity to any document chunk: {best_score:.2f} (threshold {_GAP_THRESHOLD}). Topic is required for {ctx.domain} documents.",
                    confidence=round(confidence, 3),
                    risk_score=round(section.weight * confidence, 3),
                    absence_type="coverage_gap",
                    category=ctx.domain,
                    evidence=[{"type": "ontology_mismatch", "detail": f"Required section '{section.name}' not found (similarity {best_score:.2f})"}],
                )
            )

        return candidates
