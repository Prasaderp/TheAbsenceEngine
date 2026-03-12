"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Document, AnalysisJob, AbsenceReport, Paginated } from "@/types";
import { formatDate, riskLabel, riskColor, domainLabel } from "@/lib/utils";
import { Spinner } from "@/components/ui/Spinner";
import { Badge } from "@/components/ui/Badge";
import styles from "./page.module.css";

export default function DashboardPage() {
  const { user } = useAuth();
  const [docs, setDocs] = useState<Document[]>([]);
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [reports, setReports] = useState<AbsenceReport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<Paginated<Document>>("/documents?page=1&per_page=5"),
      api.get<Paginated<AnalysisJob>>("/analysis?page=1&per_page=5"),
      api.get<Paginated<AbsenceReport>>("/reports?page=1&per_page=5"),
    ]).then(([d, j, r]) => {
      setDocs(d.data); setJobs(j.data); setReports(r.data);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className={styles.center}><Spinner size={36} /></div>;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.h1}>Welcome back, {user?.name?.split(" ")[0]}</h1>
          <p className={styles.sub}>Surface what&apos;s missing before it matters.</p>
        </div>
        <Link href="/dashboard/documents" className={styles.uploadBtn}>+ Upload Document</Link>
      </header>

      <div className={styles.grid}>
        <section className={styles.card}>
          <div className={styles.cardHead}>
            <h2>Recent Documents</h2>
            <Link href="/dashboard/documents" className={styles.seeAll}>See all →</Link>
          </div>
          {docs.length === 0 ? (
            <p className={styles.empty}>No documents yet.</p>
          ) : (
            <ul className={styles.list}>
              {docs.map(d => (
                <li key={d.id} className={styles.listItem}>
                  <span className={styles.filename}>{d.filename}</span>
                  <div className={styles.meta}>
                    <Badge label={domainLabel(d.domain)} variant="accent" />
                    <span className={styles.date}>{formatDate(d.created_at)}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className={styles.card}>
          <div className={styles.cardHead}>
            <h2>Recent Jobs</h2>
            <Link href="/dashboard/analysis" className={styles.seeAll}>See all →</Link>
          </div>
          {jobs.length === 0 ? (
            <p className={styles.empty}>No analysis jobs yet.</p>
          ) : (
            <ul className={styles.list}>
              {jobs.map(j => (
                <li key={j.id} className={styles.listItem}>
                  <Link href={`/dashboard/analysis/${j.id}`} className={styles.jobLink}>
                    <span className={styles.filename}>{j.id.slice(0, 8)}…</span>
                    <StatusBadge status={j.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className={styles.card}>
          <div className={styles.cardHead}>
            <h2>Recent Reports</h2>
            <Link href="/dashboard/reports" className={styles.seeAll}>See all →</Link>
          </div>
          {reports.length === 0 ? (
            <p className={styles.empty}>No reports yet.</p>
          ) : (
            <ul className={styles.list}>
              {reports.map(r => (
                <li key={r.id} className={styles.listItem}>
                  <Link href={`/dashboard/reports/${r.id}`} className={styles.jobLink}>
                    <span className={styles.filename}>{r.summary.slice(0, 40)}…</span>
                    <span style={{ color: riskColor(r.overall_risk_score), fontSize: "0.78rem", fontWeight: 600 }}>
                      {riskLabel(r.overall_risk_score)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: AnalysisJob["status"] }) {
  const map: Record<string, "success" | "warn" | "danger" | "default"> = {
    completed: "success", processing: "warn", pending: "default", failed: "danger",
  };
  return <Badge label={status} variant={map[status] ?? "default"} />;
}
