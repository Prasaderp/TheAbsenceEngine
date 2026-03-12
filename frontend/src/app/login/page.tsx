"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AuthProvider, useAuth } from "@/lib/auth";
import { ToastProvider, useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import styles from "./page.module.css";

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { login } = useAuth();
  const { show } = useToast();
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await login(email, password);
      show("Logged in", "success");
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally { setLoading(false); }
  }

  return (
    <div className={styles.card}>
      <div className={styles.brand}>
        <span className={styles.mark}>∅</span>
        <span className={styles.wordmark}>Absence Engine</span>
      </div>
      <h1 className={styles.title}>Sign in</h1>
      <form onSubmit={submit} className={styles.form} noValidate>
        <Input id="email" type="email" label="Email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" required />
        <Input id="password" type="password" label="Password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required />
        {error && <p className={styles.error} role="alert">{error}</p>}
        <Button type="submit" loading={loading} size="lg" style={{ width: "100%" }}>Sign in</Button>
      </form>
      <p className={styles.switch}>No account? <Link href="/register">Create one</Link></p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <AuthProvider>
      <ToastProvider>
        <div className={styles.page}>
          <LoginForm />
        </div>
      </ToastProvider>
    </AuthProvider>
  );
}
