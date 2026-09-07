"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { userFetch } from "./user-api";
import styles from "./dashboard.module.css";
type Row = {
  id: string;
  category_suggested: string;
  status: string;
  created_at: string;
  updated_at?: string;
  anonymized_text?: string;
};
const categories = [
  "Phishing/Link Berbahaya",
  "Social Engineering",
  "Penipuan Investasi",
  "Penipuan Rekrutmen",
  "Penipuan Romansa",
];

export default function Reports() {
  const [rows, setRows] = useState<Row[]>([]),
    [error, setError] = useState(""),
    [formOpen, setFormOpen] = useState(false),
    [text, setText] = useState(""),
    [category, setCategory] = useState(categories[0]),
    [consent, setConsent] = useState(false),
    [submitting, setSubmitting] = useState(false);
  const load = useCallback(() => {
    userFetch<Row[]>("/api/user/reports")
      .then(setRows)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    load();
  }, [load]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await userFetch("/api/report", {
        method: "POST",
        body: JSON.stringify({
          text,
          category_suggested: category,
          consent,
          source: "user_dashboard",
        }),
      });
      setText("");
      setConsent(false);
      setFormOpen(false);
      load();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Laporan gagal dikirim.");
    } finally {
      setSubmitting(false);
    }
  }
  return (
    <section>
      <div className={styles.pageHead}>
        <div>
          <p className={styles.kicker}>KONTRIBUSIMU</p>
          <h2>Laporan Saya</h2>
        </div>
        <button className={styles.primaryButton} onClick={() => setFormOpen(true)}>
          Kirim laporan
        </button>
      </div>
      {error ? (
        <div className={styles.state}>{error}</div>
      ) : rows.length === 0 ? (
        <div className={styles.state}>Belum ada laporan modus yang Anda kirim.</div>
      ) : (
        <div className={styles.list}>
          {rows.map((row) => (
            <article key={row.id}>
              <div>
                <small>{new Date(row.created_at).toLocaleString("id-ID")}</small>
                <h3>NG-{row.id.slice(0, 8).toUpperCase()}</h3>
                <p>{row.anonymized_text || "Teks telah diamankan."}</p>
                <b>{row.category_suggested}</b>
              </div>
              <span>{row.status.replaceAll("_", " ")}</span>
            </article>
          ))}
        </div>
      )}
      {formOpen && (
        <div
          className={styles.dialog}
          role="dialog"
          aria-modal="true"
          aria-labelledby="report-dialog-title"
        >
          <div>
            <button onClick={() => setFormOpen(false)} aria-label="Tutup formulir">
              ×
            </button>
            <p className={styles.kicker}>LAPORAN BARU</p>
            <h2 id="report-dialog-title">Laporkan pesan penipuan</h2>
            <p>Data akan dianonimkan dan ditinjau admin sebelum dapat masuk dataset publik.</p>
            <form className={styles.popupForm} onSubmit={submit}>
              <label>
                Kategori
                <select value={category} onChange={(e) => setCategory(e.target.value)}>
                  {categories.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label>
                Isi pesan
                <textarea
                  required
                  maxLength={5000}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Tempel pesan tanpa identitas pribadi…"
                />
              </label>
              <label className={styles.consentRow}>
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                />
                <span>
                  Saya menyetujui laporan disimpan, dianonimkan, ditinjau, dan bila layak digunakan
                  sebagai dataset publik.
                </span>
              </label>
              <button disabled={!consent || !text.trim() || submitting}>
                {submitting ? "Mengirim…" : "Kirim laporan"}
              </button>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
