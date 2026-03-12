"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import type { AnalysisJob } from "@/types";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import styles from "./page.module.css";

const statusVariant = (s: AnalysisJob["status"]): "success" | "warn" | "danger" | "default" =>
  ({ completed: "success", processing: "warn", pending: "default", failed: "danger" }[s] ?? "default") as never;

export default function AnalysisJobPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const done = job?.status === "completed" || job?.status === "failed";

  const fetchJob = useCallback(async () => {
    try { setJob(await api.get<AnalysisJob>(`/analysis/${jobId}`)); }
    catch { /* silently wait */ }
  }, [jobId]);

  useEffect(() => {
    fetchJob();
    const ws = new WebSocket(`ws://localhost:8000/api/v1/analysis/${jobId}/stream`);
    wsRef.current = ws;
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data) as { type: string; message?: string };
        if (msg.message) setLogs(p => [...p, msg.message!]);
        if (msg.type === "completed" || msg.type === "failed") fetchJob();
      } catch { /* ignore malformed */ }
    };
    return () => { ws.close(); };
  }, [jobId, fetchJob]);

  if (!job) return <div className={styles.center}><Spinner size={36} /></div>;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.h1}>Analysis Job</h1>
          <p className={styles.mono}>{job.id}</p>
        </div>
        <Badge label={job.status} variant={statusVariant(job.status)} />
      </div>

      <div className={styles.meta}>
        <span>Started: <strong>{job.started_at ? formatDate(job.started_at) : "—"}</strong></span>
        <span>Completed: <strong>{job.completed_at ? formatDate(job.completed_at) : "—"}</strong></span>
      </div>

      {!done && (
        <div className={styles.progress}>
          <div className={styles.progressBar} />
        </div>
      )}

      {job.error_message && (
        <div className={styles.errorBox}>
          <strong>Error:</strong> {job.error_message}
        </div>
      )}

      {logs.length > 0 && (
        <div className={styles.log}>
          {logs.map((l, i) => <div key={i} className={styles.logLine}>{l}</div>)}
        </div>
      )}

      {job.status === "completed" && (
        <div className={styles.cta}>
          <Link href={`/dashboard/analysis/${jobId}/report`}>
            <span className={styles.viewBtn}>View Absence Report →</span>
          </Link>
        </div>
      )}
    </div>
  );
}
