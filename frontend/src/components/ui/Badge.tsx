import styles from "./Badge.module.css";

type Variant = "default" | "success" | "warn" | "danger" | "accent";

interface Props { label: string; variant?: Variant; }

export function Badge({ label, variant = "default" }: Props) {
  return <span className={`${styles.badge} ${styles[variant]}`}>{label}</span>;
}
