from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from app.engine.parsers.base import ParsedDocument
from app.engine.ontologies import DomainOntology
from app.engine.embedder import EmbeddingChunk
from app.engine.llm.gateway import LLMGateway


@dataclass
class DetectionContext:
    document: ParsedDocument
    domain: str
    ontology: DomainOntology | None
    embeddings: list[EmbeddingChunk]
    llm: LLMGateway


@dataclass
class AbsenceCandidate:
    title: str
    description: str
    reasoning: str
    confidence: float
    risk_score: float
    absence_type: str
    category: str
    evidence: list[dict] = field(default_factory=list)
    suggested_completion: str | None = None


class BaseDetector(ABC):
    @abstractmethod
    async def detect(self, ctx: DetectionContext) -> list[AbsenceCandidate]: ...
