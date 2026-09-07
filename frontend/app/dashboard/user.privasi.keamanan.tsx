"use client";
import { FormEvent, useEffect, useState } from "react";
import { userFetch } from "./user-api";
import styles from "./dashboard.module.css";
type Privacy = {
  history_storage_mode: "never" | "ask" | "automatic";
  retention_period: "30_days" | "90_days" | "1_year" | "forever";
  save_anonymized_text: boolean;
  require_save_confirmation: boolean;
};
export default function Privacy() {
  const [data, setData] = useState<Privacy | null>(null),
    [loadError, setLoadError] = useState(""),
    [toast, setToast] = useState("");
  useEffect(() => {
    userFetch<Privacy>("/api/user/privacy")
      .then(setData)
      .catch((e) => setLoadError(e.message));
  }, []);
  function notify(message: string) {
    setToast(message);
    window.setTimeout(() => {
      setToast((current) => (current === message ? "" : current));
    }, 3500);
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    if (!data) return;
    try {
      setData(
        await userFetch<Privacy>("/api/user/privacy", {
          method: "PUT",
          body: JSON.stringify(data),
        }),
      );
      notify("Pengaturan privasi berhasil disimpan.");
    } catch (error) {
      notify(error instanceof Error ? error.message : "Pengaturan gagal disimpan.");
    }
  }
  async function clear() {
    if (confirm("Hapus seluruh riwayat? Tindakan tidak dapat dibatalkan.")) {
      const r = await userFetch<{ deleted: number }>("/api/user/histories", { method: "DELETE" });
      notify(`${r.deleted} riwayat berhasil dihapus.`);
    }
  }
  function download() {
    userFetch("/api/user/data-export").then((data) => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(
        new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
      );
      a.download = "data-nusaguard-saya.json";
      a.click();
      URL.revokeObjectURL(a.href);
    });
  }
  return (
    <section>
      <div className={styles.pageHead}>
        <div>
          <p className={styles.kicker}>KENDALI DATA</p>
          <h2>Privasi dan Keamanan</h2>
        </div>
      </div>
      {!data ? (
        <div className={styles.state}>{loadError || "Memuat…"}</div>
      ) : (
        <div className={styles.privacyLayout}>
          <form className={styles.settings} onSubmit={save}>
            <div className={styles.settingsHead}>
              <span aria-hidden="true">◉</span>
              <div>
                <h3>Penyimpanan riwayat</h3>
                <p>Atur kapan hasil analisis boleh disimpan di akunmu.</p>
              </div>
            </div>
            <label>
              Mode penyimpanan
              <select
                value={data.history_storage_mode}
                onChange={(e) =>
                  setData({
                    ...data,
                    history_storage_mode: e.target.value as Privacy["history_storage_mode"],
                  })
                }
              >
                <option value="ask">Selalu minta konfirmasi</option>
                <option value="automatic">Simpan otomatis</option>
                <option value="never">Jangan pernah simpan</option>
              </select>
            </label>
            <label>
              Periode penyimpanan
              <select
                value={data.retention_period}
                onChange={(e) =>
                  setData({
                    ...data,
                    retention_period: e.target.value as Privacy["retention_period"],
                  })
                }
              >
                <option value="30_days">30 hari</option>
                <option value="90_days">90 hari</option>
                <option value="1_year">1 tahun</option>
                <option value="forever">Hingga saya hapus</option>
              </select>
            </label>
            <label className={styles.switchRow}>
              <input
                type="checkbox"
                checked={data.save_anonymized_text}
                onChange={(e) => setData({ ...data, save_anonymized_text: e.target.checked })}
              />
              <span>
                <b>Simpan teks anonim</b>
                <small>Nomor, email, dan kredensial disamarkan terlebih dahulu.</small>
              </span>
            </label>
            <label className={styles.switchRow}>
              <input
                type="checkbox"
                checked={data.require_save_confirmation}
                onChange={(e) => setData({ ...data, require_save_confirmation: e.target.checked })}
              />
              <span>
                <b>Konfirmasi sebelum menyimpan</b>
                <small>NusaGuard meminta izin pada setiap hasil analisis.</small>
              </span>
            </label>
            <button>Simpan pengaturan</button>
          </form>
          <aside className={styles.privacyInfo}>
            <p className={styles.kicker}>PRIVASI SEJAK AWAL</p>
            <h3>Data tetap dalam kendalimu.</h3>
            <ul>
              <li>Analisis tidak otomatis masuk dataset publik.</li>
              <li>Teks sensitif dianonimkan sebelum disimpan.</li>
              <li>Data dapat diunduh atau dihapus kapan saja.</li>
            </ul>
          </aside>
        </div>
      )}
      <div className={styles.danger}>
        <h3>Kelola data pribadi</h3>
        <button onClick={download}>Unduh Data Saya</button>
        <button onClick={() => void clear()}>Hapus Seluruh Riwayat</button>
      </div>
      {toast && (
        <div className={styles.toast} role="status" aria-live="polite">
          <span aria-hidden="true">✓</span>
          <div>
            <b>Berhasil</b>
            <p>{toast}</p>
          </div>
        </div>
      )}
    </section>
  );
}
