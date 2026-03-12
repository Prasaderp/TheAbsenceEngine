from __future__ import annotations
import asyncio
from app.engine.parsers import get_parser
from app.engine.chunker import chunk_text
from app.engine.embedder import embed_chunks
from app.engine.classifier import classify_domain
from app.engine.ontologies import get_ontology
from app.engine.llm.factory import build_gateway
from app.engine.detectors.base import DetectionContext
from app.engine.detectors.coverage import CoverageDetector
from app.engine.detectors.implication import ImplicationDetector
from app.engine.detectors.temporal import TemporalDetector
from app.engine.detectors.relational import RelationalDetector
from app.engine.assembler import assemble
from app.shared.logger import get_logger

log = get_logger(__name__)

_DETECTORS = [CoverageDetector(), ImplicationDetector(), TemporalDetector(), RelationalDetector()]


async def run_pipeline(
    file_data: bytes,
    mime_type: str,
    domain_override: str | None = None,
) -> dict:
    llm = build_gateway()

    parser = get_parser(mime_type)
    parsed = await parser.parse(file_data, mime_type)
    log.info("parsed document", extra={"chars": len(parsed.text), "mime": mime_type})

    chunks = chunk_text(parsed.text)
    try:
        embedded = await embed_chunks(chunks, llm)
    except Exception:
        embedded = []
        log.warning("embedding failed, proceeding without embeddings")

    domain, confidence = await classify_domain(parsed.text, llm, domain_override)
    log.info("classified domain", extra={"domain": domain, "confidence": confidence})

    ontology = get_ontology(domain)

    ctx = DetectionContext(
        document=parsed,
        domain=domain,
        ontology=ontology,
        embeddings=embedded,
        llm=llm,
    )

    results = await asyncio.gather(*[d.detect(ctx) for d in _DETECTORS], return_exceptions=True)

    candidates = []
    for r in results:
        if isinstance(r, list):
            candidates.extend(r)
        else:
            log.warning("detector error", extra={"error": str(r)})

    report = await assemble(candidates, parsed.text, llm)
    report["domain_detected"] = domain
    report["domain_confidence"] = confidence
    return report
