"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import type { Document, Paginated } from "@/types";
import { formatBytes, formatDate, domainLabel } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import styles from "./page.module.css";

const ALLOWED = ["application/pdf", "text/plain", "text/markdown",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"];

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const inputRef = useRef<HTMLInputElement>(null);
  const { show } = useToast();
  const router = useRouter();

  const fetchDocs = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const res = await api.get<Paginated<Document>>(`/documents?page=${p}&per_page=20`);
      setDocs(res.data); setTotalPages(res.meta.total_pages);
    } catch { show("Failed to load documents", "error"); }
    finally { setLoading(false); }
  }, [show]);

  useEffect(() => { fetchDocs(page); }, [fetchDocs, page]);

  async function upload(file: File) {
    if (!ALLOWED.includes(file.type)) { show("File type not supported", "error"); return; }
    if (file.size > 52_428_800) { show("File exceeds 50MB limit", "error"); return; }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      await api.post("/documents", fd);
      show("Document uploaded", "success");
      fetchDocs(1);
    } catch (err: unknown) {
      show(err instanceof Error ? err.message : "Upload failed", "error");
    } finally { setUploading(false); }
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) upload(file);
  }, []);

  async function startAnalysis(docId: string) {
    try {
      const key = crypto.randomUUID();
      const job = await api.post<{ id: string }>("/analysis", { document_id: docId, idempotency_key: key });
      show("Analysis started", "success");
      router.push(`/dashboard/analysis/${job.id}`);
    } catch (err: unknown) {
      show(err instanceof Error ? err.message : "Failed to start analysis", "error");
    }
  }

  async function deleteDoc(id: string) {
    try {
      await api.del(`/documents/${id}`);
      show("Document deleted", "success");
      setDocs(p => p.filter(d => d.id !== id));
    } catch { show("Delete failed", "error"); }
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.h1}>Documents</h1>
      </header>

      <div
        className={`${styles.dropzone} ${dragging ? styles.dragging : ""}`}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        role="button" tabIndex={0} aria-label="Upload document"
        onKeyDown={e => e.key === "Enter" && inputRef.current?.click()}
      >
        <input ref={inputRef} type="file" className={styles.hidden} accept={ALLOWED.join(",")}
          onChange={e => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = ""; }} />
        {uploading ? <Spinner size={28} /> : (
          <>
            <span className={styles.dropIcon}>⬆</span>
            <span className={styles.dropText}>Drop a file or <u>browse</u></span>
            <span className={styles.dropSub}>PDF, DOCX, TXT, MD, CSV, XLSX — max 50MB</span>
          </>
        )}
      </div>

      {loading ? (
        <div className={styles.center}><Spinner size={32} /></div>
      ) : docs.length === 0 ? (
        <p className={styles.empty}>No documents. Upload one above.</p>
      ) : (
        <>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Filename</th><th>Domain</th><th>Size</th><th>Uploaded</th><th></th>
              </tr>
            </thead>
            <tbody>
              {docs.map(d => (
                <tr key={d.id}>
                  <td className={styles.name}>{d.filename}</td>
                  <td><Badge label={domainLabel(d.domain)} variant="accent" /></td>
                  <td className={styles.muted}>{formatBytes(d.size_bytes)}</td>
                  <td className={styles.muted}>{formatDate(d.created_at)}</td>
                  <td className={styles.actions}>
                    <Button size="sm" variant="secondary" onClick={() => startAnalysis(d.id)}>Analyze</Button>
                    <Button size="sm" variant="danger" onClick={() => deleteDoc(d.id)}>Delete</Button>
                  </td>
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
