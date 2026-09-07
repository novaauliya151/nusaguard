"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import AccessibilityControls from "../app/accessibility-controls";
import styles from "./public_chrome.module.css";

const links = [
  ["/", "Beranda"],
  ["/#analisis", "Analisis"],
  ["/statistics", "Statistik"],
  ["/education", "Edukasi"],
  ["/dataset", "Dataset"],
] as const;

export default function HeaderBeranda() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const [activeHref, setActiveHref] = useState(pathname);

  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [open]);

  return (
    <>
      <header className={styles.header}>
        <Link className={styles.brand} href="/" onClick={() => setOpen(false)}>
          <Image
            src="/images/logo_nusaguard.png"
            width={530}
            height={558}
            alt="Logo NusaGuard"
            priority
          />
          <b>NusaGuard</b>
        </Link>
        <button
          className={styles.menuButton}
          type="button"
          aria-label={open ? "Tutup menu" : "Buka menu"}
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
        >
          <span />
          <span />
          <span />
        </button>
        <nav className={`${styles.nav} ${open ? styles.navOpen : ""}`} aria-label="Navigasi utama">
          {links.map(([href, label]) => (
            <Link
              key={href}
              href={href}
              className={activeHref === href ? styles.active : ""}
              onClick={() => {
                setActiveHref(href);
                setOpen(false);
              }}
            >
              {label}
            </Link>
          ))}
          <Link className={styles.register} href="/register" onClick={() => setOpen(false)}>
            Daftar
          </Link>
          <Link className={styles.login} href="/login" onClick={() => setOpen(false)}>
            Masuk
          </Link>
          <div className={styles.themeControl}>
            <AccessibilityControls compact />
          </div>
        </nav>
      </header>
      {open && (
        <button
          className={styles.backdrop}
          type="button"
          aria-label="Tutup menu"
          onClick={() => setOpen(false)}
        />
      )}
    </>
  );
}
