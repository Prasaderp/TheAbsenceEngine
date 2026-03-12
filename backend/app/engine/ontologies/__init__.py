from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import yaml

_DIR = Path(__file__).parent

_DOMAIN_MAP = {
    "legal": "legal_contract.yaml",
    "product": "product_spec.yaml",
    "strategy": "strategy_doc.yaml",
    "technical": "technical_doc.yaml",
    "interpersonal": "interpersonal.yaml",
}


@dataclass
class OntologySection:
    name: str
    weight: float
    description: str


@dataclass
class DomainOntology:
    domain: str
    keywords: list[str]
    required_sections: list[OntologySection]
    required_considerations: list[str]
    stakeholders: list[str]
    temporal_considerations: list[str]


def _load(path: Path) -> DomainOntology:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return DomainOntology(
        domain=raw["domain"],
        keywords=raw.get("keywords", []),
        required_sections=[
            OntologySection(**s) for s in raw.get("required_sections", [])
        ],
        required_considerations=raw.get("required_considerations", []),
        stakeholders=raw.get("stakeholders", []),
        temporal_considerations=raw.get("temporal_considerations", []),
    )


_cache: dict[str, DomainOntology] = {}


def get_ontology(domain: str) -> DomainOntology | None:
    if domain in _cache:
        return _cache[domain]
    fname = _DOMAIN_MAP.get(domain)
    if not fname:
        return None
    ontology = _load(_DIR / fname)
    _cache[domain] = ontology
    return ontology


def load_all() -> dict[str, DomainOntology]:
    for domain, fname in _DOMAIN_MAP.items():
        if domain not in _cache:
            _cache[domain] = _load(_DIR / fname)
    return _cache
