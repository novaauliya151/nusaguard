export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";
export type AnalyzeResponse = { kategori_dasar: "spam" | "ham"; category: string; risk_level: RiskLevel; risk_score: number; confidence: number; nseae_scores: Record<string, number>; detected_patterns: {pattern:string;weight:number}[]; explanation: string; recommendation: string; model_source: "indobert" | "rules-fallback" };
export type CategoryInfo = { slug:string; name:string; description:string; examples:string[]; prevention:string[] };
