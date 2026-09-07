import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import "./mobile.css";
import "./accessibility.css";
import PublicShell from "../components/public_shell";

export const metadata: Metadata = {
  title: "NusaGuard — Periksa Sebelum Percaya",
  description: "Analisis pola penipuan berbahasa Indonesia dengan IndoBERT dan N-SEAE.",
  icons: {
    icon: "/images/logo_nusaguard.png",
    apple: "/images/logo_nusaguard.png",
  },
};

type RootLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="id" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <PublicShell>{children}</PublicShell>
      </body>
    </html>
  );
}
