"use client";

import {
  Activity,
  BarChart3,
  BookOpen,
  Bot,
  ChartNoAxesColumnIncreasing,
  CircleUserRound,
  Database,
  FileText,
  House,
  LogOut,
  Menu,
  Settings,
  Users,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";
import LogoNusaGuard from "../../components/logo_nusaguard";
import type { AdminUser } from "./admin-api";
import styles from "./admin.module.css";

export const ADMIN_NAV = [
  ["dashboard", "Dashboard", "dashboard.view"],
  ["users", "Manajemen Pengguna", "users.view"],
  ["reports", "Laporan Modus", "reports.view"],
  ["dataset", "Dataset", "datasets.view"],
  ["nseae", "Validasi N-SEAE", "nseae.validate"],
  ["education", "Konten Edukasi", "education.view"],
  ["statistics", "Statistik", "statistics.view"],
  ["model", "Monitoring Model", "models.view"],
  ["activities", "Log Aktivitas", "activity_logs.view"],
  ["profile", "Profil", "profile.manage"],
] as const;

type NavId = (typeof ADMIN_NAV)[number][0];

const NAV_ICONS: Record<NavId, LucideIcon> = {
  dashboard: House,
  users: Users,
  reports: FileText,
  dataset: Database,
  nseae: ChartNoAxesColumnIncreasing,
  education: BookOpen,
  statistics: BarChart3,
  model: Bot,
  activities: Activity,
  profile: CircleUserRound,
};

type AdminSidebarProps = {
  open: boolean;
  feature: string;
  user: AdminUser;
  onClose: () => void;
  onLogout: () => void;
};

export default function AdminSidebar({
  open,
  feature,
  user,
  onClose,
  onLogout,
}: AdminSidebarProps) {
  const visible = ADMIN_NAV.filter(
    ([id, , permission]) => id !== "profile" && user.permissions.includes(permission),
  );

  useEffect(() => {
    if (!open) return;
    const closeWithEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.body.classList.add(styles.adminSidebarLocked);
    document.addEventListener("keydown", closeWithEscape);
    return () => {
      document.body.classList.remove(styles.adminSidebarLocked);
      document.removeEventListener("keydown", closeWithEscape);
    };
  }, [open, onClose]);

  return (
    <>
      <button
        className={`${styles.sidebarBackdrop} ${open ? styles.visible : ""}`}
        onClick={onClose}
        aria-label="Tutup navigasi admin"
        tabIndex={open ? 0 : -1}
      />
      <aside className={`${styles.sidebar} ${open ? styles.open : ""}`}>
        <div className={styles.logo}>
          <LogoNusaGuard />
          <div>
            <b>NusaGuard</b>
            <small>ADMIN CONSOLE</small>
          </div>
        </div>
        <nav>
          {visible.map(([id, label]) => {
            const NavIcon = NAV_ICONS[id];
            return (
              <Link
                title={label}
                key={id}
                href={id === "dashboard" ? "/admin" : `/admin?fitur=${id}`}
                className={feature === id ? styles.active : ""}
                onClick={onClose}
              >
                <NavIcon className={styles.navIcon} aria-hidden="true" />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>
        <div className={styles.adminAccount}>
          <span className={styles.avatar}>{user.name.slice(0, 2).toUpperCase()}</span>
          <div>
            <b>{user.name}</b>
            <small>{user.role.replaceAll("_", " ")}</small>
          </div>
          <details className={styles.adminAccountMenu}>
            <summary aria-label="Buka menu akun admin">
              <Settings aria-hidden="true" />
            </summary>
            <div>
              <Link href="/admin?fitur=profile" onClick={onClose}>
                <CircleUserRound aria-hidden="true" />
                Profil
              </Link>
              <button onClick={onLogout}>
                <LogOut aria-hidden="true" />
                Keluar
              </button>
            </div>
          </details>
        </div>
      </aside>
    </>
  );
}

export function AdminMenuIcon() {
  return <Menu aria-hidden="true" />;
}
