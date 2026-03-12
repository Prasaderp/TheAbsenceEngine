import pytest
from unittest.mock import AsyncMock, MagicMock
from app.engine.chunker import chunk_text, Chunk
from app.engine.embedder import cosine_similarity, embed_chunks, semantic_search, EmbeddingChunk
from app.engine.classifier import _rule_based, classify_domain
from app.engine.ontologies import get_ontology, load_all
from app.engine.assembler import assemble, _risk


def test_chunk_text_basic():
    text = "Hello world. " * 200
    chunks = chunk_text(text, max_chars=500, overlap_chars=100)
    assert len(chunks) > 1
    for i, c in enumerate(chunks):
        assert c.index == i
        assert len(c.text) > 0


def test_chunk_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_overlap():
    text = "A" * 1000
    chunks = chunk_text(text, max_chars=400, overlap_chars=100)
    for i in range(1, len(chunks)):
        assert chunks[i].char_start < chunks[i - 1].char_end


def test_cosine_similarity():
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert cosine_similarity(a, b) == pytest.approx(1.0)
    c = [0.0, 1.0, 0.0]
    assert cosine_similarity(a, c) == pytest.approx(0.0)


def test_cosine_similarity_zero():
    assert cosine_similarity([0.0], [1.0]) == 0.0


@pytest.mark.asyncio
async def test_embed_chunks():
    mock_llm = AsyncMock()
    mock_llm.embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
    chunks = [Chunk(0, "hello", 0, 5), Chunk(1, "world", 6, 11)]
    result = await embed_chunks(chunks, mock_llm)
    assert len(result) == 2
    assert result[0].embedding == [0.1, 0.2]


def test_semantic_search():
    query = [1.0, 0.0]
    corpus = [
        EmbeddingChunk(Chunk(0, "a", 0, 1), [1.0, 0.0]),
        EmbeddingChunk(Chunk(1, "b", 1, 2), [0.0, 1.0]),
        EmbeddingChunk(Chunk(2, "c", 2, 3), [0.7, 0.7]),
    ]
    results = semantic_search(query, corpus, top_k=2)
    assert results[0][0].chunk.index == 0
    assert len(results) == 2


def test_rule_based_legal():
    text = "WHEREAS the parties agree to indemnify each other under governing law..."
    domain, conf = _rule_based(text)
    assert domain == "legal"
    assert conf > 0.3


def test_rule_based_product():
    text = "User story: As a product manager I want to track sprint velocity and KPI metrics for the MVP."
    domain, conf = _rule_based(text)
    assert domain == "product"


def test_rule_based_no_match():
    domain, conf = _rule_based("The quick brown fox jumps over the lazy dog.")
    assert conf == 0.0 or domain is None


@pytest.mark.asyncio
async def test_classify_domain_override():
    mock_llm = AsyncMock()
    domain, conf = await classify_domain("any text", mock_llm, domain_override="legal")
    assert domain == "legal"
    assert conf == 1.0
    mock_llm.generate_structured.assert_not_called()


def test_ontology_load_all():
    ontologies = load_all()
    assert "legal" in ontologies
    assert "product" in ontologies
    assert "strategy" in ontologies
    assert "technical" in ontologies
    assert "interpersonal" in ontologies


def test_legal_ontology_structure():
    ont = get_ontology("legal")
    assert ont is not None
    assert ont.domain == "legal"
    assert len(ont.required_sections) > 0
    assert any(s.name == "payment_terms" for s in ont.required_sections)
    assert len(ont.stakeholders) > 0


def test_unknown_ontology():
    assert get_ontology("unknown_domain") is None


def test_risk_scoring():
    from app.engine.detectors.base import AbsenceCandidate
    c = AbsenceCandidate(
        title="test",
        description="desc",
        reasoning="reason",
        confidence=0.9,
        risk_score=0.8,
        absence_type="coverage_gap",
        category="legal",
    )
    score = _risk(c)
    assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_assemble_empty():
    mock_llm = AsyncMock()
    result = await assemble([], "some text", mock_llm)
    assert result["overall_risk_score"] == 0.0
    assert result["items"] == []


@pytest.mark.asyncio
async def test_assemble_dedup():
    from app.engine.detectors.base import AbsenceCandidate
    mock_llm = AsyncMock()
    mock_llm.embed.return_value = [[1.0, 0.0], [0.99, 0.01]]
    mock_llm.generate.return_value = MagicMock(text="Suggested text.")

    cands = [
        AbsenceCandidate("Gap A", "desc", "reason", 0.9, 0.8, "coverage_gap", "legal"),
        AbsenceCandidate("Gap A duplicate", "desc", "reason", 0.7, 0.6, "coverage_gap", "legal"),
    ]
    result = await assemble(cands, "doc text", mock_llm)
    assert len(result["items"]) == 1
    assert result["items"][0]["confidence"] == 0.9
