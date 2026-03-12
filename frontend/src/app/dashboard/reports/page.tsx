"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { AbsenceReport, Paginated } from "@/types";
import { formatDate, riskLabel, riskColor, domainLabel } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/Toast";
import styles from "./page.module.css";

export default function ReportsPage() {
  const [reports, setReports] = useState<AbsenceReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const { show } = useToast();

  const fetchReports = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const res = await api.get<Paginated<AbsenceReport>>(`/reports?page=${p}&per_page=20`);
      setReports(res.data); setTotalPages(res.meta.total_pages);
    } catch { show("Failed to load reports", "error"); }
    finally { setLoading(false); }
  }, [show]);

  useEffect(() => { fetchReports(page); }, [fetchReports, page]);

  async function deleteReport(id: string) {
    try {
      await api.del(`/reports/${id}`);
      show("Deleted", "success");
      setReports(p => p.filter(r => r.id !== id));
    } catch { show("Delete failed", "error"); }
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.h1}>Reports</h1>
      {loading ? <div className={styles.center}><Spinner size={32} /></div> :
        reports.length === 0 ? <p className={styles.empty}>No reports yet.</p> : (
          <>
            <div className={styles.grid}>
              {reports.map(r => (
                <div key={r.id} className={styles.card}>
                  <div className={styles.cardTop}>
                    <Badge label={domainLabel(r.domain_detected)} variant="accent" />
                    <span className={styles.date}>{formatDate(r.created_at)}</span>
                  </div>
                  <p className={styles.summary}>{r.summary.slice(0, 100)}…</p>
                  <div className={styles.cardBottom}>
                    <span className={styles.risk} style={{ color: riskColor(r.overall_risk_score) }}>
                      ● {riskLabel(r.overall_risk_score)} Risk
                    </span>
                    <div className={styles.cardActions}>
                      <Link href={`/dashboard/reports/${r.id}`}>
                        <Button size="sm" variant="secondary">View</Button>
                      </Link>
                      <Button size="sm" variant="danger" onClick={() => deleteReport(r.id)}>Delete</Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {totalPages > 1 && (
              <div className={styles.pagination}>
                <Button size="sm" variant="ghost" disabled={page === 1} onClick={() => setPage(p => p - 1)}>← Prev</Button>
                <span className={styles.muted}>{page} / {totalPages}</span>
                <Button size="sm" variant="ghost" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>Next →</Button>
              </div>
            )}
          </>
        )
      }
    </div>
  );
}
