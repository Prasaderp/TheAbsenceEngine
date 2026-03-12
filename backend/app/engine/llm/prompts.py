CLASSIFY_DOMAIN = """Analyze the following document excerpt and classify its domain.

Document (first 2000 tokens):
{text}

Return JSON matching the schema provided."""

EXTRACT_ASSERTIONS = """Extract all key factual claims, commitments, and assumptions from this document.
For each, identify what logical follow-up topics or provisions that claim necessitates.

Document:
{text}

Return JSON matching the schema provided."""

COVERAGE_VERIFY = """A document analysis identified a potential gap: "{topic}".

Document excerpt:
{excerpt}

Is this topic adequately addressed in the document? Consider implicit references and different terminology.
Return JSON matching the schema provided."""

TEMPORAL_EXTRACT = """Extract all temporal references, future scenarios, and time-bounded commitments from this document.
Identify any significant timeframes or future conditions the document does NOT address.

Document:
{text}

Domain: {domain}

Return JSON matching the schema provided."""

RELATIONAL_EXTRACT = """Analyze the relational and sentiment context for each entity mentioned in this document.
Identify entities that are mentioned purely transactionally with no evaluative, collaborative, or relational framing.

Document:
{text}

Return JSON matching the schema provided."""

SUGGEST_COMPLETION = """Based on this document context and identified absence, draft content that addresses the gap.
Match the document's tone, style, and terminology exactly.

Document excerpt:
{excerpt}

Identified absence: {title}
Description: {description}

Draft a concise paragraph (2-5 sentences) addressing this gap:"""
