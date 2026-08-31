import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import "./mobile.css";
import "./accessibility.css";
import AccessibilityControls from "./accessibility-controls";

export const metadata: Metadata = {
  title: "NusaGuard — Periksa Sebelum Percaya",
  description: "Analisis pola penipuan berbahasa Indonesia dengan IndoBERT dan N-SEAE.",
};

type RootLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="id" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}<AccessibilityControls/></body>
    </html>
  );
}


