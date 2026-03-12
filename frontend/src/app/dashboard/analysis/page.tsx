"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { AnalysisJob, Paginated } from "@/types";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/Toast";
import styles from "./page.module.css";

const statusVariant = (s: AnalysisJob["status"]): "success" | "warn" | "danger" | "default" =>
  ({ completed: "success", processing: "warn", pending: "default", failed: "danger" }[s] ?? "default") as "success" | "warn" | "danger" | "default";

export default function AnalysisPage() {
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const { show } = useToast();

  const fetch = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const res = await api.get<Paginated<AnalysisJob>>(`/analysis?page=${p}&per_page=20`);
      setJobs(res.data); setTotalPages(res.meta.total_pages);
    } catch { show("Failed to load jobs", "error"); }
    finally { setLoading(false); }
  }, [show]);

  useEffect(() => { fetch(page); }, [fetch, page]);

  return (
    <div className={styles.page}>
      <h1 className={styles.h1}>Analysis Jobs</h1>

      {loading ? (
        <div className={styles.center}><Spinner size={32} /></div>
      ) : jobs.length === 0 ? (
        <p className={styles.empty}>No analysis jobs. <Link href="/dashboard/documents">Upload a document</Link> to get started.</p>
      ) : (
        <>
          <table className={styles.table}>
            <thead>
              <tr><th>Job ID</th><th>Status</th><th>Domain</th><th>Started</th><th>Completed</th><th></th></tr>
            </thead>
            <tbody>
              {jobs.map(j => (
                <tr key={j.id}>
                  <td className={styles.mono}>{j.id.slice(0, 8)}…</td>
                  <td><Badge label={j.status} variant={statusVariant(j.status)} /></td>
                  <td className={styles.muted}>{j.domain_override ?? "auto"}</td>
                  <td className={styles.muted}>{j.started_at ? formatDate(j.started_at) : "—"}</td>
                  <td className={styles.muted}>{j.completed_at ? formatDate(j.completed_at) : "—"}</td>
                  <td><Link href={`/dashboard/analysis/${j.id}`}><Badge label="View" variant="accent" /></Link></td>
                </tr>
              ))}
            </tbody>
          </table>
          {totalPages > 1 && (
            <div className={styles.pagination}>
              <Button size="sm" variant="ghost" disabled={page === 1} onClick={() => setPage(p => p - 1)}>← Prev</Button>
              <span className={styles.muted}>{page} / {totalPages}</span>
              <Button size="sm" variant="ghost" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>Next →</Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
