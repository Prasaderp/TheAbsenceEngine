import styles from "./Input.module.css";

interface Props extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, id, className = "", ...rest }: Props) {
  return (
    <div className={styles.wrap}>
      {label && <label htmlFor={id} className={styles.label}>{label}</label>}
      <input id={id} className={`${styles.input} ${error ? styles.errored : ""} ${className}`} {...rest} />
      {error && <span className={styles.error} role="alert">{error}</span>}
    </div>
  );
}
