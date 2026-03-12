"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import styles from "./Sidebar.module.css";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: "⊞" },
  { href: "/dashboard/documents", label: "Documents", icon: "◫" },
  { href: "/dashboard/analysis", label: "Analysis", icon: "◈" },
  { href: "/dashboard/reports", label: "Reports", icon: "◉" },
  { href: "/dashboard/schemas", label: "Schemas", icon: "⬡" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <span className={styles.logoMark}>∅</span>
        <span className={styles.logoText}>Absence<br /><em>Engine</em></span>
      </div>

      <nav className={styles.nav} aria-label="Main navigation">
        {nav.map(({ href, label, icon }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link key={href} href={href} className={`${styles.item} ${active ? styles.active : ""}`}>
              <span className={styles.icon}>{icon}</span>
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className={styles.user}>
        <div className={styles.avatar}>{user?.name?.[0]?.toUpperCase() ?? "?"}</div>
        <div className={styles.userInfo}>
          <span className={styles.userName}>{user?.name}</span>
          <span className={styles.userEmail}>{user?.email}</span>
        </div>
        <button onClick={logout} className={styles.logout} aria-label="Sign out" title="Sign out">⏻</button>
      </div>
    </aside>
  );
}
