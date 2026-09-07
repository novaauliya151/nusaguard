"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import FooterBeranda from "./footer_beranda";
import HeaderBeranda from "./header_beranda";
import styles from "./public_chrome.module.css";

export default function PublicShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isDashboard = pathname.startsWith("/admin") || pathname.startsWith("/dashboard");
  if (isDashboard) return children;

  return (
    <div className={styles.site}>
      <HeaderBeranda />
      <div className={styles.content}>{children}</div>
      <FooterBeranda />
    </div>
  );
}
