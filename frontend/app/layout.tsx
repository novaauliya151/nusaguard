import type { Metadata } from "next";
import "./globals.css";
import "./mobile.css";
import "./accessibility.css";
import AccessibilityControls from "./accessibility-controls";

export const metadata: Metadata = {
  title: "NusaGuard — Periksa Sebelum Percaya",
  description: "Analisis pola penipuan berbahasa Indonesia dengan IndoBERT dan N-SEAE.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="id" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}<AccessibilityControls/></body>
    </html>
  );
}

