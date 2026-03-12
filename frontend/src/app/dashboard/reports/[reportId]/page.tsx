"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { AbsenceReport } from "@/types";
import { Spinner } from "@/components/ui/Spinner";
import ReportView from "@/components/features/ReportView";

export default function ReportDetailPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const [report, setReport] = useState<AbsenceReport | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<AbsenceReport>(`/reports/${reportId}`)
      .then(setReport)
      .catch(e => setError(e instanceof Error ? e.message : "Not found"));
  }, [reportId]);

  if (error) return <p style={{ color: "var(--danger)", padding: "24px" }}>{error}</p>;
  if (!report) return <div style={{ display: "flex", justifyContent: "center", padding: 80 }}><Spinner size={36} /></div>;
  return <ReportView report={report} />;
}
