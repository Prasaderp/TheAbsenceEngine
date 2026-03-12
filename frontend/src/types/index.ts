export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  domain: string | null;
  domain_confidence: number | null;
  created_at: string;
}

export interface AnalysisJob {
  id: string;
  document_id: string;
  user_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  idempotency_key: string;
  domain_override: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface AbsenceItem {
  id: string;
  report_id: string;
  category: string;
  title: string;
  description: string;
  reasoning: string;
  confidence: number;
  risk_score: number;
  absence_type: string;
  evidence: Record<string, unknown>[];
  sort_order: number;
  suggested_completion?: string | null;
}

export interface AbsenceReport {
  id: string;
  job_id: string;
  document_id: string;
  user_id: string;
  summary: string;
  overall_risk_score: number;
  domain_detected: string;
  items: AbsenceItem[];
  created_at: string;
}

export interface Paginated<T> {
  data: T[];
  meta: { page: number; per_page: number; total: number; total_pages: number };
}

export interface ApiError {
  error: { code: string; message: string; request_id: string };
}

export interface CustomSchema {
  id: string;
  user_id: string;
  name: string;
  domain: string;
  schema_definition: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
