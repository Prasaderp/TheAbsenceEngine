from __future__ import annotations
from pydantic import BaseModel
from app.engine.llm.gateway import LLMGateway
from app.engine.llm.prompts import CLASSIFY_DOMAIN

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "legal": ["WHEREAS", "indemnify", "governing law", "termination", "hereinafter", "jurisdiction", "covenant", "warranty"],
    "product": ["user story", "acceptance criteria", "sprint", "backlog", "persona", "feature", "MVP", "KPI"],
    "strategy": ["competitive advantage", "market share", "SWOT", "OKR", "go-to-market", "TAM", "SAM"],
    "technical": ["architecture", "API", "endpoint", "schema", "deployment", "scalability", "SLA", "RFC"],
    "interpersonal": ["feedback", "growth", "collaboration", "1:1", "performance review", "recognition"],
}

VALID_DOMAINS = {"legal", "product", "strategy", "technical", "interpersonal", "general"}


class _ClassifyResult(BaseModel):
    domain: str
    confidence: float
    reasoning: str


def _rule_based(text: str) -> tuple[str | None, float]:
    sample = text[:5000].lower()
    scores: dict[str, int] = {}
    for domain, kws in _DOMAIN_KEYWORDS.items():
        scores[domain] = sum(1 for kw in kws if kw.lower() in sample)
    best = max(scores, key=lambda d: scores[d])
    total = sum(scores.values())
    if total == 0 or scores[best] == 0:
        return None, 0.0
    return best, min(scores[best] / max(total, 1) + 0.3, 0.95)


async def classify_domain(
    text: str,
    llm: LLMGateway,
    domain_override: str | None = None,
) -> tuple[str, float]:
    if domain_override and domain_override in VALID_DOMAINS:
        return domain_override, 1.0

    rule_domain, rule_conf = _rule_based(text)
    prompt = CLASSIFY_DOMAIN.format(text=text[:8000])

    try:
        result = await llm.generate_structured(prompt, _ClassifyResult)
        llm_domain = result.domain if result.domain in VALID_DOMAINS else "general"
        llm_conf = max(0.0, min(1.0, result.confidence))
    except Exception:
        return rule_domain or "general", rule_conf

    if rule_domain == llm_domain:
        return llm_domain, min((rule_conf + llm_conf) / 2 + 0.1, 0.99)

    if llm_conf >= 0.7:
        return llm_domain, llm_conf

    return rule_domain or llm_domain, max(rule_conf, llm_conf) * 0.8
