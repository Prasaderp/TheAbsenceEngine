CLASSIFY_DOMAIN = """You are a document classification expert. Analyze this document excerpt and classify its domain.

Valid domains (choose exactly one):
- legal: contracts, agreements, NDAs, terms of service, compliance docs
- product: PRDs, user stories, feature specs, product requirements
- strategy: business plans, competitive analysis, go-to-market, OKRs
- technical: architecture docs, API specs, RFCs, runbooks, design docs
- interpersonal: meeting notes, performance reviews, 1:1 notes, team retrospectives
- general: anything that doesn't clearly fit the above categories

Document excerpt:
{text}

Evaluate keyword density, structural patterns, and terminology. Return JSON matching the schema provided."""

EXTRACT_ASSERTIONS = """You are a logical analysis expert. Extract the most important factual claims, commitments, assumptions, and promises from this document. For each, identify what logical consequences, follow-up provisions, or unanswered questions that claim necessitates.

Focus on:
- Explicit commitments (SLAs, timelines, deliverables)
- Stated assumptions that require validation
- Claims that create obligations or dependencies
- Promises that require enforcement mechanisms

Limit to the 15 most significant assertions. For each assertion, provide up to 5 implications.

Document:
{text}

Return JSON matching the schema provided."""

COVERAGE_VERIFY = """You are a document completeness expert. A gap analysis identified that the topic "{topic}" may be missing from a document.

Document excerpt:
{excerpt}

Determine whether this topic is adequately addressed. Consider:
- Explicit coverage under different terminology or headings
- Implicit coverage through related provisions
- Partial coverage that may be insufficient

Be conservative: only mark as addressed if the topic is meaningfully covered, not merely mentioned in passing.

Return JSON matching the schema provided."""

TEMPORAL_EXTRACT = """You are a temporal analysis expert. Analyze this document for temporal blind spots — timeframes, future scenarios, lifecycle phases, or contingencies that are never addressed.

Domain: {domain}
Domain-specific temporal areas to check: {temporal_hints}

Document:
{text}

Identify gaps such as:
- What happens after expiry/completion/termination
- Contingency plans for delays or failures
- Long-term horizon considerations (12+ months)
- Transition periods and handoff scenarios
- Renewal, extension, or exit processes
- Seasonal or cyclical factors

Return up to 10 gaps, ordered by severity. Return JSON matching the schema provided."""

RELATIONAL_EXTRACT = """You are a stakeholder and relational analysis expert. Analyze entities (people, roles, organizations, teams) mentioned in this document for relational blind spots.

Document:
{text}

Identify entities that are mentioned only in transactional/operational context but never in evaluative, collaborative, or relational dimensions such as:
- Trust, accountability, or feedback mechanisms
- Growth, development, or capacity building
- Conflict resolution or escalation paths
- Performance evaluation or recognition
- Collaboration quality or communication patterns

Return JSON matching the schema provided."""

STAKEHOLDER_EXTRACT = """Identify all stakeholders, personas, roles, and entities that this document references or implies. Then compare against these expected stakeholders for the domain: {stakeholders}

Document:
{text}

For each expected stakeholder not adequately represented in the document, explain why their absence matters and what risks it creates.

Return JSON matching the schema provided."""

SUGGEST_COMPLETION = """Based on this document context and identified absence, draft content that addresses the gap. Match the document's tone, style, and terminology exactly.

Document excerpt:
{excerpt}

Identified absence: {title}
Description: {description}

Draft a concise paragraph (2-5 sentences) addressing this gap:"""
