"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import styles from "./page.module.css";

const DOMAINS = ["legal", "product", "strategy", "technical", "interpersonal"];

export default function NewSchemaPage() {
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("legal");
  const [sections, setSections] = useState("");
  const [considerations, setConsiderations] = useState("");
  const [loading, setLoading] = useState(false);
  const { show } = useToast();
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const schema_definition = {
        required_sections: sections.split("\n").map(s => s.trim()).filter(Boolean),
        required_considerations: considerations.split("\n").map(s => s.trim()).filter(Boolean),
      };
      await api.post("/schemas", { name, domain, schema_definition });
      show("Schema created", "success");
      router.push("/dashboard/schemas");
    } catch (err: unknown) {
      show(err instanceof Error ? err.message : "Failed to create", "error");
    } finally { setLoading(false); }
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.h1}>New Schema</h1>
      <form onSubmit={submit} className={styles.form}>
        <Input id="schema-name" label="Name" value={name} onChange={e => setName(e.target.value)} required placeholder="e.g. My NDA Template" />
        <div className={styles.field}>
          <label htmlFor="schema-domain" className={styles.label}>Domain</label>
          <select id="schema-domain" className={styles.select} value={domain} onChange={e => setDomain(e.target.value)}>
            {DOMAINS.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
          </select>
        </div>
        <div className={styles.field}>
          <label htmlFor="schema-sections" className={styles.label}>Required Sections (one per line)</label>
          <textarea id="schema-sections" className={styles.textarea} value={sections} onChange={e => setSections(e.target.value)} rows={6} placeholder="e.g.\nscope_of_work\npayment_terms\ntermination_clause" />
        </div>
        <div className={styles.field}>
          <label htmlFor="schema-considerations" className={styles.label}>Required Considerations (one per line)</label>
          <textarea id="schema-considerations" className={styles.textarea} value={considerations} onChange={e => setConsiderations(e.target.value)} rows={4} placeholder="e.g.\ndata_breach_liability\nsubcontractor_provisions" />
        </div>
        <div className={styles.actions}>
          <Button type="submit" loading={loading}>Create Schema</Button>
          <Button type="button" variant="ghost" onClick={() => router.push("/dashboard/schemas")}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}
