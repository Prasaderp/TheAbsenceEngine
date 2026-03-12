import styles from "./Spinner.module.css";
export function Spinner({ size = 24 }: { size?: number }) {
  return <span className={styles.spin} style={{ width: size, height: size }} aria-label="Loading" role="status" />;
}
