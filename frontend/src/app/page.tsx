import Link from "next/link";
import styles from "./page.module.css";

export default function LandingPage() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.mark}>∅</span>
          <span className={styles.wordmark}>Absence Engine</span>
        </div>
        <nav className={styles.nav}>
          <Link href="/login" className={styles.navLink}>Sign in</Link>
          <Link href="/register" className={styles.cta}>Get started →</Link>
        </nav>
      </header>

      <main className={styles.hero}>
        <div className={styles.badge}>AI-Powered Document Analysis</div>
        <h1 className={styles.heroTitle}>
          Find what&apos;s missing<br />
          <span className={styles.accent}>before it matters.</span>
        </h1>
        <p className={styles.heroCopy}>
          Upload any document — contracts, PRDs, strategy docs, code — and surface the structured negative space:
          missing clauses, unaddressed stakeholders, logical gaps, temporal blind spots.
        </p>
        <div className={styles.heroActions}>
          <Link href="/register" className={styles.primaryBtn}>Start analyzing →</Link>
          <Link href="/login" className={styles.ghostBtn}>I have an account</Link>
        </div>

        <div className={styles.features}>
          {[
            { icon: "◈", title: "Coverage Gaps", desc: "Compare your document against domain ontologies and peer corpora." },
            { icon: "⟳", title: "Logical Implications", desc: "Every assertion implies follow-up provisions. Find the ones you missed." },
            { icon: "◷", title: "Temporal Absences", desc: "Identify time horizons, contingencies, and future states never addressed." },
            { icon: "◉", title: "Stakeholder Gaps", desc: "Who is mentioned? Who should be — but isn't?" },
          ].map(f => (
            <div key={f.title} className={styles.feature}>
              <span className={styles.featureIcon}>{f.icon}</span>
              <h3 className={styles.featureTitle}>{f.title}</h3>
              <p className={styles.featureDesc}>{f.desc}</p>
            </div>
          ))}
        </div>
      </main>

      <footer className={styles.footer}>
        <span>© 2026 The Absence Engine</span>
      </footer>
    </div>
  );
}
