"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { CustomSchema, Paginated } from "@/types";
import { formatDate, domainLabel } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/Toast";
import styles from "./page.module.css";

export default function SchemasPage() {
  const [schemas, setSchemas] = useState<CustomSchema[]>([]);
  const [loading, setLoading] = useState(true);
  const { show } = useToast();

  const fetchSchemas = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<Paginated<CustomSchema>>("/schemas?page=1&per_page=50");
      setSchemas(res.data);
    } catch { show("Failed to load schemas", "error"); }
    finally { setLoading(false); }
  }, [show]);

  useEffect(() => { fetchSchemas(); }, [fetchSchemas]);

  async function del(id: string) {
    try {
      await api.del(`/schemas/${id}`);
      show("Deleted", "success");
      setSchemas(p => p.filter(s => s.id !== id));
    } catch { show("Delete failed", "error"); }
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.h1}>Custom Schemas</h1>
        <Link href="/dashboard/schemas/new"><Button size="sm">+ New Schema</Button></Link>
      </div>
      {loading ? <div className={styles.center}><Spinner size={32} /></div> :
        schemas.length === 0 ? <p className={styles.empty}>No custom schemas.</p> : (
          <table className={styles.table}>
            <thead><tr><th>Name</th><th>Domain</th><th>Created</th><th></th></tr></thead>
            <tbody>
              {schemas.map(s => (
                <tr key={s.id}>
                  <td className={styles.name}>{s.name}</td>
                  <td><Badge label={domainLabel(s.domain)} variant="accent" /></td>
                  <td className={styles.muted}>{formatDate(s.created_at)}</td>
                  <td><Button size="sm" variant="danger" onClick={() => del(s.id)}>Delete</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      }
    </div>
  );
}
