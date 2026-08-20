"use client";

import { useState } from "react";
import type { AnalyzeResponse } from "./types";

export default function Home() {
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    if (!message.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, source: "manual_web" }),
      });

      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data: AnalyzeResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError("Gagal menghubungi server. Pastikan backend sedang berjalan.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">NusaGuard — Cek Pesan</h1>

        <textarea
          className="w-full border rounded-lg p-3 h-32"
          placeholder="Tempel pesan WhatsApp yang mencurigakan di sini..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="mt-3 bg-blue-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
        >
          {loading ? "Menganalisis..." : "Analisis Pesan"}
        </button>

        {error && <p className="mt-4 text-red-600">{error}</p>}

        {result && (
          <div className="mt-6 border rounded-lg p-4 bg-white">
            <p className="font-semibold">
              Risk Level: <span>{result.risk_level}</span> ({Math.round(result.risk_score * 100)}/100)
            </p>
            <p>Kategori: {result.kategori_nusaguard}</p>
            <p className="text-sm text-gray-600 mt-1">
              Confidence model: {Math.round(result.confidence * 100)}%
            </p>

            <div className="mt-3">
              <p className="font-medium">Indikator N-SEAE:</p>
              <ul className="text-sm mt-1 space-y-1">
                {result.detected_patterns.map((p) => (
                  <li key={p.pattern}>
                    {p.pattern}: {Math.round((p.weight ?? 0) * 100)}%
                  </li>
                ))}
              </ul>
            </div>

            <p className="mt-3 text-sm">{result.explanation}</p>
          </div>
        )}
      </div>
    </main>
  );
}