"use client";
import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { AbsenceReport, AbsenceItem } from "@/types";
import { riskColor, riskLabel, domainLabel, absenceTypeLabel, formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import styles from "./ReportView.module.css";

function RiskGauge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const r = 40, cx = 50, cy = 50, stroke = 8;
  const circ = 2 * Math.PI * r;
  const dashOffset = circ * (1 - score);
  const color = riskColor(score);

  return (
    <div className={styles.gauge}>
      <svg viewBox="0 0 100 100" className={styles.gaugeSvg}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--border)" strokeWidth={stroke} />
        <circle
          cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={stroke}
          strokeDasharray={circ} strokeDashoffset={dashOffset}
          strokeLinecap="round"
          style={{ transform: "rotate(-90deg)", transformOrigin: "center", transition: "stroke-dashoffset 0.8s ease" }}
        />
        <text x="50" y="46" textAnchor="middle" fill={color} style={{ fontSize: "1.4em", fontWeight: 700, fontFamily: "var(--font)" }}>
          {pct}
        </text>
        <text x="50" y="60" textAnchor="middle" fill="var(--text-3)" style={{ fontSize: "0.55em" }}>
          {riskLabel(score)}
        </text>
      </svg>
    </div>
  );
}

function AbsenceCard({ item }: { item: AbsenceItem }) {
  const [open, setOpen] = useState(false);
  const color = riskColor(item.risk_score);

  return (
    <div className={styles.card} style={{ borderLeftColor: color }}>
      <button className={styles.cardHead} onClick={() => setOpen(o => !o)} aria-expanded={open}>
        <div className={styles.cardLeft}>
          <span className={styles.cardTitle}>{item.title}</span>
          <div className={styles.cardMeta}>
            <Badge label={absenceTypeLabel(item.absence_type)} variant="default" />
            <Badge label={item.category} variant="accent" />
          </div>
        </div>
        <div className={styles.cardRight}>
          <span className={styles.riskNum} style={{ color }}>{Math.round(item.risk_score * 100)}</span>
          <span className={styles.chevron}>{open ? "▲" : "▼"}</span>
        </div>
      </button>

      {open && (
        <div className={styles.cardBody}>
          <p className={styles.desc}>{item.description}</p>
          <div className={styles.section}>
            <span className={styles.sectionLabel}>Reasoning</span>
            <p className={styles.desc}>{item.reasoning}</p>
          </div>
          {item.suggested_completion && (
            <div className={styles.section}>
              <span className={styles.sectionLabel}>Suggested Completion</span>
              <p className={styles.suggestion}>{item.suggested_completion}</p>
            </div>
          )}
          {item.evidence.length > 0 && (
            <div className={styles.section}>
              <span className={styles.sectionLabel}>Evidence</span>
              <ul className={styles.evidence}>
                {item.evidence.map((e, i) => (
                  <li key={i}>{String(e.detail ?? JSON.stringify(e))}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ReportView({ report }: { report: AbsenceReport }) {
  const { show } = useToast();
  const [exporting, setExporting] = useState(false);

  async function exportJson() {
    setExporting(true);
    try {
      const res = await fetch(`/api/v1/reports/${report.id}/export?format=json`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = `report-${report.id}.json`; a.click();
      URL.revokeObjectURL(url);
    } catch { show("Export failed", "error"); }
    finally { setExporting(false); }
  }

  return (
    <div className={styles.page}>
      <div className={styles.hero}>
        <div className={styles.heroLeft}>
          <div className={styles.heroMeta}>
            <Badge label={domainLabel(report.domain_detected)} variant="accent" />
            <span className={styles.date}>{formatDate(report.created_at)}</span>
          </div>
          <h1 className={styles.heroTitle}>Absence Report</h1>
          <p className={styles.summary}>{report.summary}</p>
          <div className={styles.stats}>
            <div className={styles.stat}><span className={styles.statVal}>{report.items.length}</span><span className={styles.statLabel}>Absences</span></div>
            <div className={styles.stat}><span className={styles.statVal}>{domainLabel(report.domain_detected)}</span><span className={styles.statLabel}>Domain</span></div>
          </div>
          <div className={styles.actions}>
            <Button size="sm" variant="secondary" onClick={exportJson} loading={exporting}>Export JSON</Button>
            <Link href={`/api/v1/reports/${report.id}/export?format=pdf`} target="_blank">
              <Button size="sm" variant="secondary">Export PDF</Button>
            </Link>
          </div>
        </div>
        <RiskGauge score={report.overall_risk_score} />
      </div>

      <div className={styles.items}>
        <h2 className={styles.sectionTitle}>Detected Absences</h2>
        {report.items.length === 0 ? (
          <p className={styles.empty}>No absences detected — this document appears complete.</p>
        ) : (
          report.items.map(item => <AbsenceCard key={item.id} item={item} />)
        )}
      </div>
    </div>
  );
}
