export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));
}

export function riskColor(score: number): string {
  if (score >= 0.8) return "var(--risk-critical)";
  if (score >= 0.6) return "var(--risk-high)";
  if (score >= 0.4) return "var(--risk-medium)";
  return "var(--risk-low)";
}

export function riskLabel(score: number): string {
  if (score >= 0.8) return "Critical";
  if (score >= 0.6) return "High";
  if (score >= 0.4) return "Medium";
  return "Low";
}

export function domainLabel(domain: string | null): string {
  const map: Record<string, string> = {
    legal: "Legal", product: "Product", strategy: "Strategy",
    technical: "Technical", interpersonal: "Interpersonal",
  };
  return domain ? (map[domain] ?? domain) : "Unknown";
}

export function absenceTypeLabel(t: string): string {
  const map: Record<string, string> = {
    coverage_gap: "Coverage Gap", logical_implication: "Logical Implication",
    temporal_gap: "Temporal Gap", emotional_relational: "Relational",
    stakeholder_gap: "Stakeholder Gap", structural_gap: "Structural Gap",
  };
  return map[t] ?? t;
}
