"use client";
import { useEffect, useRef, useState } from "react";
import type { AnalyzeResponse } from "../types";
import { API, userFetch } from "./user-api";
import styles from "./dashboard.module.css";
const riskLabels = { LOW: "Rendah", MEDIUM: "Sedang", HIGH: "Tinggi" } as const;
const reasonLabels: Record<string, string> = {
  urgency: "Pesan mendorong kamu untuk bertindak terburu-buru.",
  authority: "Pengirim mengatasnamakan lembaga atau pihak berwenang.",
  fear: "Pesan menggunakan ancaman atau membuat penerima merasa takut.",
  reward: "Pesan menawarkan hadiah atau keuntungan yang perlu diwaspadai.",
  impersonation: "Ada tanda bahwa pengirim mungkin menyamar sebagai orang lain.",
  credential_request: "Pesan meminta data rahasia atau informasi pribadi.",
};
function riskLabel(level: AnalyzeResponse["risk_level"]) {
  return riskLabels[level];
}
function resultHeading(result: AnalyzeResponse) {
  return result.category === "Aman"
    ? "Tidak ditemukan tanda penipuan yang kuat"
    : `Pesan terindikasi ${result.category}`;
}
function resultSummary(result: AnalyzeResponse) {
  if (result.category === "Aman")
    return "Pesan ini terlihat aman berdasarkan pemeriksaan saat ini. Tetap pastikan identitas pengirim sebelum membagikan data pribadi.";
  if (result.risk_level === "HIGH")
    return "Pesan ini memiliki beberapa tanda berbahaya. Jangan ikuti permintaannya sebelum memastikan kebenaran pengirim.";
  if (result.risk_level === "MEDIUM")
    return "Pesan ini memiliki tanda yang perlu diperiksa lebih lanjut. Jangan terburu-buru mengambil tindakan.";
  return "Risikonya terlihat rendah, tetapi tetap periksa pengirim dan jangan membagikan informasi rahasia.";
}
function detectedReasons(result: AnalyzeResponse) {
  return result.detected_patterns
    .map(({ pattern }) => reasonLabels[pattern])
    .filter((reason): reason is string => Boolean(reason));
}
export default function UserAnalysis() {
  const [message, setMessage] = useState(""),
    [result, setResult] = useState<AnalyzeResponse | null>(null),
    [analyzedText, setAnalyzedText] = useState(""),
    [save, setSave] = useState(false),
    [saveText, setSaveText] = useState(true),
    [privacyMode, setPrivacyMode] = useState<"never" | "ask" | "automatic">("ask"),
    [status, setStatus] = useState(""),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false),
    requestId = useRef(0);
  useEffect(() => {
    userFetch<{
      history_storage_mode: "never" | "ask" | "automatic";
      save_anonymized_text: boolean;
    }>("/api/user/privacy")
      .then((privacy) => {
        setPrivacyMode(privacy.history_storage_mode);
        setSave(privacy.history_storage_mode === "automatic");
        setSaveText(privacy.save_anonymized_text);
      })
      .catch(() => setError("Pengaturan privasi belum dapat dimuat."));
  }, []);
  async function analyze() {
    const text = message.trim();
    if (!text) return;
    const currentRequest = ++requestId.current;
    setResult(null);
    setAnalyzedText("");
    setLoading(true);
    setError("");
    setStatus("");
    try {
      const response = await fetch(`${API}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, source: "user_dashboard" }),
      });
      if (!response.ok) throw new Error();
      const body: AnalyzeResponse = await response.json();
      if (currentRequest !== requestId.current) return;
      setResult(body);
      setAnalyzedText(text);
      if (save) await persist(body, text);
    } catch {
      if (currentRequest === requestId.current)
        setError("Analisis gagal. Periksa koneksi backend.");
    } finally {
      if (currentRequest === requestId.current) setLoading(false);
    }
  }
  async function persist(body = result, text = analyzedText) {
    if (!body || !text) return;
    await userFetch("/api/user/histories", {
      method: "POST",
      body: JSON.stringify({
        text,
        save_text: saveText,
        category: body.category,
        risk_level: body.risk_level,
        risk_score: body.risk_score,
        confidence: body.confidence,
        summary: body.explanation,
        explanation: body.explanation,
        warning_signs: body.detected_patterns.map((x) => x.pattern),
        recommendations: body.recommendation,
        nseae_scores: body.nseae_scores,
        model_version: body.model_source,
      }),
    });
    setStatus("Hasil anonim berhasil disimpan ke Riwayat Saya.");
  }
  return (
    <section>
      <div className={styles.pageHead}>
        <div>
          <p className={styles.kicker}>ANALISIS PRIBADI</p>
          <h2>Analisis Pesan Baru</h2>
        </div>
      </div>
      <div className={styles.analyzer}>
        <div>
          <textarea
            maxLength={5000}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Tempel pesan mencurigakan…"
          />
          <label>
            <input
              type="checkbox"
              checked={save}
              disabled={privacyMode !== "ask"}
              onChange={(e) => setSave(e.target.checked)}
            />{" "}
            Simpan hasil ini ke Riwayat Saya
          </label>
          {save && (
            <label>
              <input
                type="checkbox"
                checked={saveText}
                onChange={(e) => setSaveText(e.target.checked)}
              />{" "}
              Sertakan preview teks yang sudah dianonimkan
            </label>
          )}
          <small>
            {privacyMode === "automatic"
              ? "Penyimpanan otomatis aktif sesuai pengaturan Privasi dan Keamanan."
              : privacyMode === "never"
                ? "Penyimpanan riwayat dinonaktifkan melalui Privasi dan Keamanan."
                : "Teks asli tidak pernah disimpan. Kamu menentukan penyimpanan setiap kali menganalisis."}
          </small>
          <div className={styles.meta}>
            <span>{message.length}/5000</span>
            <button disabled={loading || !message.trim()} onClick={() => void analyze()}>
              {loading ? "Menganalisis…" : "Analisis sekarang"}
            </button>
          </div>
          {error && <p className={styles.error}>{error}</p>}
          {status && <p>{status}</p>}
        </div>
        <div
          className={`${styles.result} ${result ? styles[result.risk_level.toLowerCase()] : ""}`}
        >
          {!result ? (
            <div className={styles.empty}>
              <span>⌁</span>
              <h3>{loading ? "Menganalisis pesan terbaru…" : "Hasil muncul di sini"}</h3>
              <p>
                {loading
                  ? "Hasil sebelumnya telah dikosongkan."
                  : "Analisis berjalan tanpa harus disimpan."}
              </p>
            </div>
          ) : (
            <>
              <span>TINGKAT RISIKO</span>
              <strong>
                {Math.round(result.risk_score * 100)}%<small> perkiraan bahaya</small>
              </strong>
              <p className={styles.riskLevelText}>Risiko {riskLabel(result.risk_level)}</p>
              <h3>{resultHeading(result)}</h3>
              <p>{resultSummary(result)}</p>
              <div className={styles.riskScale} aria-label="Panduan tingkat risiko">
                <span>
                  Rendah
                  <br />
                  Tetap waspada
                </span>
                <span>
                  Sedang
                  <br />
                  Periksa kembali
                </span>
                <span>
                  Tinggi
                  <br />
                  Jangan lanjutkan
                </span>
              </div>
              {detectedReasons(result).length > 0 && (
                <div className={styles.reasons}>
                  <b>Mengapa hasilnya seperti ini?</b>
                  <ul>
                    {detectedReasons(result).map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className={styles.recommend}>
                <b>Yang sebaiknya kamu lakukan</b>
                <p>{result.recommendation}</p>
              </div>
              {!save && (
                <button onClick={() => void persist()}>Simpan hasil secara opsional</button>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
