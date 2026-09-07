"use client";

import Link from "next/link";
import { useEffect, type ReactNode } from "react";
import LogoNusaGuard from "../../components/logo_nusaguard";
import styles from "./dashboard.module.css";

export type UserView =
  | "ringkasan"
  | "analisis"
  | "riwayat"
  | "laporan"
  | "panduan"
  | "profil"
  | "privasi";

type IconName = "home" | "search" | "history" | "report" | "bookmark" | "shield";

export const USER_MENUS: Array<{ key: UserView; icon: IconName; label: string }> = [
  { key: "ringkasan", icon: "home", label: "Dashboard" },
  { key: "analisis", icon: "search", label: "Analisis Baru" },
  { key: "riwayat", icon: "history", label: "Riwayat Analisis" },
  { key: "laporan", icon: "report", label: "Laporan Saya" },
  { key: "panduan", icon: "bookmark", label: "Panduan Tersimpan" },
  { key: "privasi", icon: "shield", label: "Privasi dan Keamanan" },
];

type AppSidebarUserProps = {
  open: boolean;
  activeView: UserView;
  user: { name: string };
  onClose: () => void;
  onNavigate: (view: UserView) => void;
  onProfile: () => void;
  onLogout: () => void;
};

function SidebarIcon({ name }: { name: IconName }) {
  const paths: Record<IconName, ReactNode> = {
    home: (
      <>
        <path d="m3 11 9-8 9 8" />
        <path d="M5 10v10h14V10" />
        <path d="M9 20v-6h6v6" />
      </>
    ),
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),
    history: (
      <>
        <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
        <path d="M3 3v5h5" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    report: (
      <>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
        <path d="M14 2v6h6" />
        <path d="M8 13h8M8 17h5" />
      </>
    ),
    bookmark: <path d="M6 3h12v18l-6-4-6 4Z" />,
    shield: (
      <>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
  };

  return (
    <svg className={styles.navIcon} viewBox="0 0 24 24" aria-hidden="true">
      {paths[name]}
    </svg>
  );
}

export function MenuIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M18 6 6 18M6 6l12 12" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.6v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" />
    </svg>
  );
}

function ProfileIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M10 17l5-5-5-5M15 12H3" />
      <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
    </svg>
  );
}

export default function UserSidebar({
  open,
  activeView,
  user,
  onClose,
  onNavigate,
  onProfile,
  onLogout,
}: AppSidebarUserProps) {
  useEffect(() => {
    if (!open) return;
    const closeWithEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.body.classList.add(styles.sidebarLocked);
    document.addEventListener("keydown", closeWithEscape);
    return () => {
      document.body.classList.remove(styles.sidebarLocked);
      document.removeEventListener("keydown", closeWithEscape);
    };
  }, [open, onClose]);

  return (
    <>
      <button
        className={styles.backdrop}
        onClick={onClose}
        aria-label="Tutup menu navigasi"
        aria-hidden={!open}
        tabIndex={open ? 0 : -1}
      />
      <aside id="user-sidebar" aria-label="Navigasi dashboard pengguna">
        <div className={styles.sideHead}>
          <Link className={styles.logo} href="/" onClick={onClose}>
            <LogoNusaGuard />
            <b>NusaGuard</b>
          </Link>
          <button className={styles.closeMenu} onClick={onClose} aria-label="Tutup sidebar">
            <CloseIcon />
          </button>
        </div>
        <nav aria-label="Menu pengguna">
          {USER_MENUS.map(({ key, icon, label }) => (
            <button
              key={key}
              className={activeView === key ? styles.active : ""}
              onClick={() => onNavigate(key)}
              aria-current={activeView === key ? "page" : undefined}
            >
              <SidebarIcon name={icon} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className={styles.account}>
          <i aria-hidden="true">{user.name.slice(0, 2).toUpperCase()}</i>
          <div>
            <b>{user.name}</b>
            <small>Pengguna</small>
          </div>
          <details className={styles.accountMenu}>
            <summary aria-label="Buka menu akun">
              <SettingsIcon />
            </summary>
            <div>
              <button onClick={onProfile}>
                <ProfileIcon />
                <span>Profil</span>
              </button>
              <button onClick={onLogout}>
                <LogoutIcon />
                <span>Keluar</span>
              </button>
            </div>
          </details>
        </div>
      </aside>
    </>
  );
}
