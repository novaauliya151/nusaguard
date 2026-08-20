export type NSEAEPattern = {
  pattern: string;
  weight: number | null;
};

export type AnalyzeResponse = {
  kategori_dasar: "spam" | "ham";
  kategori_nusaguard: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  risk_score: number;
  confidence: number;
  detected_patterns: NSEAEPattern[];
  explanation: string;
};