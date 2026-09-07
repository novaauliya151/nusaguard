"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import { useCallback, useEffect, useMemo, useState } from "react";
import { API, userFetch } from "./user-api";
import styles from "./dashboard.module.css";

type Guide = {
  id: string;
  title: string;
  category: string;
  description: string;
  warning_signs?: string[];
  prevention?: string[];
};

export default function Guides() {
  const [guides, setGuides] = useState<Guide[]>([]);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [importantOnly, setImportantOnly] = useState(false);
  const [detail, setDetail] = useState<Guide | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [educationResponse, saved] = await Promise.all([
        fetch(`${API}/api/education`),
        userFetch<Guide[]>("/api/user/saved-guides"),
      ]);
      if (!educationResponse.ok) throw new Error("Panduan sistem belum dapat dimuat.");
      setGuides(await educationResponse.json());
      setSavedIds(new Set(saved.map((item) => item.id)));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Panduan gagal dimuat.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const categories = useMemo(
    () => [...new Set(guides.map((guide) => guide.category))].sort(),
    [guides],
  );
  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase("id-ID");
    return guides.filter((guide) => {
      const matchesQuery =
        !normalizedQuery ||
        `${guide.title} ${guide.description}`.toLocaleLowerCase("id-ID").includes(normalizedQuery);
      return (
        matchesQuery &&
        (!category || guide.category === category) &&
        (!importantOnly || savedIds.has(guide.id))
      );
    });
  }, [guides, savedIds, query, category, importantOnly]);

  async function toggleImportant(guide: Guide) {
    const saved = savedIds.has(guide.id);
    await userFetch(`/api/user/saved-guides/${guide.id}`, { method: saved ? "DELETE" : "POST" });
    setSavedIds((current) => {
      const next = new Set(current);
      if (saved) next.delete(guide.id);
      else next.add(guide.id);
      return next;
    });
  }

  return (
    <section>
      <div className={styles.pageHead}>
        <div>
          <p className={styles.kicker}>PANDUAN DARI SISTEM</p>
          <h2>Panduan Keamanan</h2>
          <p>Cari panduan lalu tandai yang penting agar mudah ditemukan kembali.</p>
        </div>
      </div>
      <div className={styles.guideFilters}>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Cari judul atau isi panduan"
        />
        <select value={category} onChange={(event) => setCategory(event.target.value)}>
          <option value="">Semua kategori</option>
          {categories.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
        <label className={styles.importantFilter}>
          <input
            type="checkbox"
            checked={importantOnly}
            onChange={(event) => setImportantOnly(event.target.checked)}
          />
          Panduan Berbintang
        </label>
      </div>
      {loading ? (
        <div className={styles.state}>Memuat panduan sistem…</div>
      ) : error ? (
        <div className={styles.state}>{error}</div>
      ) : filtered.length === 0 ? (
        <div className={styles.state}>Panduan tidak ditemukan.</div>
      ) : (
        <div className={styles.guideGrid}>
          {filtered.map((guide) => (
            <article key={guide.id}>
              <div className={styles.guideCardHead}>
                <small>{guide.category}</small>
                <button
                  className={savedIds.has(guide.id) ? styles.starActive : ""}
                  onClick={() => void toggleImportant(guide)}
                  title={savedIds.has(guide.id) ? "Hapus dari penting" : "Tandai penting"}
                  aria-label={savedIds.has(guide.id) ? "Hapus dari penting" : "Tandai penting"}
                >
                  ★
                </button>
              </div>
              <h3>{guide.title}</h3>
              <p>{guide.description}</p>
              <button className={styles.textButton} onClick={() => setDetail(guide)}>
                Baca panduan
              </button>
            </article>
          ))}
        </div>
      )}
      {detail && (
        <div className={styles.dialog} role="dialog" aria-modal="true">
          <div>
            <button onClick={() => setDetail(null)} aria-label="Tutup panduan">
              ×
            </button>
            <p className={styles.kicker}>{detail.category}</p>
            <h2>{detail.title}</h2>
            <p>{detail.description}</p>
            {detail.warning_signs?.length ? (
              <>
                <h3>Tanda peringatan</h3>
                <ul>
                  {detail.warning_signs.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            ) : null}
            {detail.prevention?.length ? (
              <>
                <h3>Langkah pencegahan</h3>
                <ul>
                  {detail.prevention.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            ) : null}
          </div>
        </div>
      )}
    </section>
  );
}
