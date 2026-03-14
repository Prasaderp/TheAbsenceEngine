from __future__ import annotations
from pydantic import BaseModel
from app.engine.detectors.base import BaseDetector, DetectionContext, AbsenceCandidate
from app.engine.embedder import semantic_search
from app.engine.llm.prompts import COVERAGE_VERIFY, STAKEHOLDER_EXTRACT

_GAP_THRESHOLD = 0.55
_WEAK_COVERAGE_THRESHOLD = 0.70


class _VerifyResult(BaseModel):
    is_addressed: bool
    explanation: str
    confidence: float


class _StakeholderGap(BaseModel):
    stakeholder: str
    reasoning: str
    severity: float


class _StakeholderResult(BaseModel):
    gaps: list[_StakeholderGap]


class CoverageDetector(BaseDetector):
    async def detect(self, ctx: DetectionContext) -> list[AbsenceCandidate]:
        if not ctx.ontology:
            return []

        candidates: list[AbsenceCandidate] = []
        candidates.extend(await self._check_sections(ctx))
        candidates.extend(await self._check_considerations(ctx))
        candidates.extend(await self._check_stakeholders(ctx))
        return candidates

    async def _check_sections(self, ctx: DetectionContext) -> list[AbsenceCandidate]:
        results: list[AbsenceCandidate] = []
        for section in ctx.ontology.required_sections:
            best_score = 0.0

            if ctx.embeddings:
                try:
                    query_emb = await ctx.llm.embed([section.description])
                    top = semantic_search(query_emb[0], ctx.embeddings, top_k=3)
                    best_score = top[0][1] if top else 0.0
                except Exception:
                    pass

            if best_score >= _WEAK_COVERAGE_THRESHOLD:
                continue

            excerpt = ctx.document.text[:2000] if best_score < _GAP_THRESHOLD else ""
            if ctx.embeddings and best_score >= _GAP_THRESHOLD:
                try:
                    query_emb = await ctx.llm.embed([section.description])
                    top = semantic_search(query_emb[0], ctx.embeddings, top_k=2)
                    excerpt = "\n".join(h.chunk.text[:500] for h, _ in top) if top else ctx.document.text[:2000]
                except Exception:
                    excerpt = ctx.document.text[:2000]

            prompt = COVERAGE_VERIFY.format(topic=section.description, excerpt=excerpt)
            try:
                result = await ctx.llm.generate_structured(prompt, _VerifyResult)
                if result.is_addressed:
                    continue
                confidence = max(0.1, min(1.0, result.confidence * (1.0 - best_score * 0.5)))
            except Exception:
                confidence = max(0.3, (1.0 - best_score) * 0.7)

            results.append(
                AbsenceCandidate(
                    title=f"Missing: {section.name.replace('_', ' ').title()}",
                    description=section.description,
                    reasoning=f"Required section for {ctx.domain} documents. Semantic match: {best_score:.2f} (threshold: {_GAP_THRESHOLD}).",
                    confidence=round(confidence, 3),
                    risk_score=round(section.weight * confidence, 3),
                    absence_type="coverage_gap",
                    category=ctx.domain,
                    evidence=[{"type": "ontology_mismatch", "detail": f"Required section '{section.name}' — similarity {best_score:.2f}"}],
                )
            )
        return results

    async def _check_considerations(self, ctx: DetectionContext) -> list[AbsenceCandidate]:
        results: list[AbsenceCandidate] = []
        text_lower = ctx.document.text[:15000].lower()

        for consideration in ctx.ontology.required_considerations:
            tokens = consideration.lower().replace("_", " ").split()
            matched = sum(1 for t in tokens if t in text_lower)
            keyword_score = matched / max(len(tokens), 1)

            if keyword_score >= 0.6:
                continue

            if ctx.embeddings:
                try:
                    query_emb = await ctx.llm.embed([consideration.replace("_", " ")])
                    top = semantic_search(query_emb[0], ctx.embeddings, top_k=2)
                    best_score = top[0][1] if top else 0.0
                    if best_score >= _WEAK_COVERAGE_THRESHOLD:
                        continue
                except Exception:
                    pass

            confidence = round(max(0.3, 1.0 - keyword_score) * 0.75, 3)
            results.append(
                AbsenceCandidate(
                    title=f"Missing consideration: {consideration.replace('_', ' ').title()}",
                    description=f"The document does not address '{consideration.replace('_', ' ')}', which is a standard consideration for {ctx.domain} documents.",
                    reasoning=f"Keyword match score: {keyword_score:.2f}. This consideration is expected in {ctx.domain} documents.",
                    confidence=confidence,
                    risk_score=round(confidence * 0.7, 3),
                    absence_type="coverage_gap",
                    category=ctx.domain,
                    evidence=[{"type": "consideration_missing", "detail": consideration}],
                )
            )
        return results

    async def _check_stakeholders(self, ctx: DetectionContext) -> list[AbsenceCandidate]:
        if not ctx.ontology.stakeholders:
            return []

        stakeholder_list = ", ".join(ctx.ontology.stakeholders)
        prompt = STAKEHOLDER_EXTRACT.format(
            stakeholders=stakeholder_list,
            text=ctx.document.text[:10000],
        )
        try:
            result = await ctx.llm.generate_structured(prompt, _StakeholderResult)
        except Exception:
            return []

        results: list[AbsenceCandidate] = []
        for gap in result.gaps[:8]:
            sev = max(0.0, min(1.0, gap.severity))
            results.append(
                AbsenceCandidate(
                    title=f"Missing stakeholder: {gap.stakeholder}",
                    description=gap.reasoning,
                    reasoning=f"Expected stakeholder '{gap.stakeholder}' for {ctx.domain} documents is not adequately represented.",
                    confidence=round(sev * 0.85, 3),
                    risk_score=round(sev * 0.7, 3),
                    absence_type="stakeholder_gap",
                    category=ctx.domain,
                    evidence=[{"type": "stakeholder_missing", "detail": gap.stakeholder}],
                )
            )
        return results
