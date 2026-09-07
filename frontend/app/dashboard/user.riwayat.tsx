"use client";
/* eslint-disable react-hooks/set-state-in-effect */
import { useCallback, useEffect, useState } from "react";
import { userFetch } from "./user-api";
import styles from "./dashboard.module.css";
type Row = {
  id: string;
  safe_title: string;
  summary: string;
  category: string;
  risk_level: string;
  risk_score: number;
  is_favorite: boolean;
  created_at: string;
};
const categories = [
  "Aman",
  "Phishing/Link Berbahaya",
  "Social Engineering",
  "Penipuan Investasi",
  "Penipuan Rekrutmen",
  "Penipuan Romansa",
];

function ActionIcon({ name }: { name: "detail" | "important" | "delete" }) {
  if (name === "detail")
    return (
      <svg viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="3" />
        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
      </svg>
    );
  if (name === "important")
    return (
      <svg viewBox="0 0 24 24">
        <path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9Z" />
      </svg>
    );
  return (
    <svg viewBox="0 0 24 24">
      <path d="M3 6h18M8 6V4h8v2M19 6l-1 15H6L5 6M10 11v6M14 11v6" />
    </svg>
  );
}

export default function History() {
  const [rows, setRows] = useState<Row[]>([]),
    [q, setQ] = useState(""),
    [category, setCategory] = useState(""),
    [risk, setRisk] = useState(""),
    [important, setImportant] = useState(false),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [detail, setDetail] = useState<Row | null>(null);
  const load = useCallback(() => {
    setLoading(true);
    userFetch<Row[]>(
      `/api/user/histories?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}&risk=${risk}${important ? "&favorite=true" : ""}`,
    )
      .then(setRows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [q, category, risk, important]);
  useEffect(() => {
    void load();
  }, [load]);
  async function update(row: Row, patch: object) {
    await userFetch(`/api/user/histories/${row.id}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    });
    await load();
  }
  async function remove(row: Row) {
    if (confirm("Hapus riwayat ini? Tindakan tidak dapat dibatalkan.")) {
      await userFetch(`/api/user/histories/${row.id}`, { method: "DELETE" });
      await load();
    }
  }
  return (
    <section>
      <div className={styles.pageHead}>
        <div>
          <p className={styles.kicker}>DATA MILIKMU</p>
          <h2>Riwayat Analisis</h2>
        </div>
      </div>
      <div className={styles.filters}>
        <input
          placeholder="Cari kategori atau ringkasan aman"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select value={risk} onChange={(e) => setRisk(e.target.value)}>
          <option value="">Semua risiko</option>
          <option>LOW</option>
          <option>MEDIUM</option>
          <option>HIGH</option>
        </select>
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">Semua kategori</option>
          {categories.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
        <label className={styles.importantFilter}>
          <input
            type="checkbox"
            checked={important}
            onChange={(e) => setImportant(e.target.checked)}
          />
          Panduan Berbintang
        </label>
        <button
          onClick={() => {
            setQ("");
            setRisk("");
            setCategory("");
            setImportant(false);
          }}
        >
          Reset
        </button>
      </div>
      {loading ? (
        <div className={styles.state}>Memuat riwayat…</div>
      ) : error ? (
        <div className={styles.state}>{error}</div>
      ) : rows.length === 0 ? (
        <div className={styles.state}>
          Belum ada riwayat yang disimpan. Analisis tanpa disimpan tetap dapat dilakukan kapan saja.
        </div>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.historyTable}>
            <thead>
              <tr>
                <th>Tanggal</th>
                <th>Ringkasan</th>
                <th>Kategori</th>
                <th>Risiko</th>
                <th>Status</th>
                <th>Aksi</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>{new Date(row.created_at).toLocaleDateString("id-ID")}</td>
                  <td>
                    <b>{row.safe_title}</b>
                    <small>{row.summary}</small>
                  </td>
                  <td>{row.category}</td>
                  <td>
                    <span className={styles[`risk${row.risk_level}`]}>
                      {row.risk_level} · {Math.round(row.risk_score * 100)}
                    </span>
                  </td>
                  <td>
                    {row.is_favorite ? (
                      <span className={styles.importantBadge}>★ Penting</span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    <div className={styles.iconActions}>
                      <button
                        data-tooltip="Lihat detail"
                        aria-label="Lihat detail"
                        onClick={() => setDetail(row)}
                      >
                        <ActionIcon name="detail" />
                      </button>
                      <button
                        data-tooltip={row.is_favorite ? "Hapus tanda penting" : "Tandai penting"}
                        aria-label={row.is_favorite ? "Hapus tanda penting" : "Tandai penting"}
                        onClick={() => void update(row, { is_favorite: !row.is_favorite })}
                      >
                        <ActionIcon name="important" />
                      </button>
                      <button
                        data-tooltip="Hapus riwayat"
                        aria-label="Hapus riwayat"
                        onClick={() => void remove(row)}
                      >
                        <ActionIcon name="delete" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {detail && (
        <div className={styles.dialog}>
          <div>
            <button onClick={() => setDetail(null)}>×</button>
            <p className={styles.kicker}>DETAIL RIWAYAT</p>
            <h2>{detail.safe_title}</h2>
            <p>{detail.summary}</p>
            <p>
              <b>Kategori:</b> {detail.category}
            </p>
            <p>
              <b>Risiko:</b> {detail.risk_level} ({Math.round(detail.risk_score * 100)}/100)
            </p>
            <small>Hasil AI merupakan alat bantu, bukan keputusan mutlak.</small>
          </div>
        </div>
      )}
    </section>
  );
}
