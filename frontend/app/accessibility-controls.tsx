"use client";
/* eslint-disable react-hooks/set-state-in-effect -- persisted theme is restored only after hydration */
import { useEffect, useState } from "react";
const KEY = "nusaguard_theme";
export default function AccessibilityControls({ compact = false }: { compact?: boolean }) {
  const [dark, setDark] = useState(false),
    [mounted, setMounted] = useState(false);
  useEffect(() => {
    const saved = localStorage.getItem(KEY) === "dark";
    setDark(saved);
    document.documentElement.classList.toggle("dark", saved);
    document.documentElement.style.colorScheme = saved ? "dark" : "light";
    setMounted(true);
  }, []);
  function toggle() {
    const next = !dark;
    setDark(next);
    localStorage.setItem(KEY, next ? "dark" : "light");
    document.documentElement.classList.toggle("dark", next);
    document.documentElement.style.colorScheme = next ? "dark" : "light";
  }
  return (
    <button
      className={`theme-toggle ${compact ? "theme-toggle--compact" : ""}`}
      onClick={toggle}
      aria-pressed={mounted && dark}
      aria-label={dark ? "Gunakan tema terang" : "Gunakan tema gelap"}
      title={dark ? "Tema terang" : "Tema gelap"}
    >
      <span aria-hidden className="theme-toggle__icon">
        {dark ? (
          <svg viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24">
            <path d="M20.5 15.2A8.5 8.5 0 0 1 8.8 3.5 8.5 8.5 0 1 0 20.5 15.2Z" />
          </svg>
        )}
      </span>
      {!compact && <span>{dark ? "Terang" : "Gelap"}</span>}
    </button>
  );
}
