"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import styles from "./admin.module.css";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const categoryColors: Record<string, string> = {
  "Phishing/Link Berbahaya": "#ff6b58",
  "Social Engineering": "#f4ad4d",
  "Penipuan Investasi": "#9e7df5",
  "Penipuan Rekrutmen": "#49a4e8",
  "Penipuan Romansa": "#eb70a0",
  Aman: "#65c88b",
};

type Report = { id: string; text: string; category_suggested: string; status: "pending" | "reviewed" | "rejected"; created_at: string };
type Dashboard = { total_analyzed: number; category_counts: Record<string, number>; reports_total: number; reports_pending: number; recent_reports: Report[]; model_status: string; privacy_mode: string };

export default function AdminPage() {
  const [key, setKey] = useState("");
  const [draftKey, setDraftKey] = useState("");
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const load = useCallback(async (adminKey: string) => {
    setLoading(true); setError("");
    try {
      const response = await fetch(`${API}/api/admin/dashboard`, { headers: { "X-API-Key": adminKey } });
      if (!response.ok) throw new Error(response.status === 401 ? "Kunci admin tidak valid." : "Dashboard belum dapat dimuat. Periksa backend dan ADMIN_API_KEY.");
      setData(await response.json()); setKey(adminKey); sessionStorage.setItem("nusaguard_admin_key", adminKey);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Terjadi kesalahan."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const saved = sessionStorage.getItem("nusaguard_admin_key");
    if (!saved) return;
    const timer = window.setTimeout(() => void load(saved), 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  const submit = (event: FormEvent) => { event.preventDefault(); if (draftKey.trim()) void load(draftKey.trim()); };
  const logout = () => { sessionStorage.removeItem("nusaguard_admin_key"); setKey(""); setData(null); setDraftKey(""); };

  async function moderate(id: string, status: "reviewed" | "rejected") {
    const response = await fetch(`${API}/api/admin/reports/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json", "X-API-Key": key }, body: JSON.stringify({ status }) });
    if (response.ok) await load(key); else setError("Status laporan gagal diperbarui.");
  }

  const categoryRows = useMemo(() => {
    if (!data) return [];
    const total = Math.max(data.total_analyzed, 1);
    return Object.entries(categoryColors).map(([name, color]) => ({ name, color, count: data.category_counts[name] ?? 0, percent: Math.round(((data.category_counts[name] ?? 0) / total) * 100) })).sort((a,b) => b.count-a.count);
  }, [data]);

  if (!data) return <main className={styles.loginShell}><section className={styles.loginCard}>
    <div className={styles.loginBrand}><span>NG</span><div><b>NusaGuard</b><small>ADMIN CONSOLE</small></div></div>
    <p className={styles.kicker}>AREA TERLINDUNGI</p><h1>Masuk ke pusat kendali.</h1><p>Pantau tren penipuan dan moderasi laporan sukarela tanpa menyimpan histori analisis pengguna.</p>
    <form onSubmit={submit}><label htmlFor="admin-key">Kunci admin</label><input id="admin-key" type="password" autoComplete="current-password" value={draftKey} onChange={e=>setDraftKey(e.target.value)} placeholder="Masukkan ADMIN_API_KEY"/><button disabled={loading || !draftKey.trim()}>{loading ? "Memverifikasi…" : "Masuk ke dashboard →"}</button></form>
    {error && <p className={styles.loginError} role="alert">{error}</p>}<Link href="/">← Kembali ke pemeriksa publik</Link>
  </section><div className={styles.loginVisual}><span>PRIVACY-FIRST OPERATIONS</span><div className={styles.rings}><i/><i/><b>N</b></div><p>Data yang terlihat di sini hanya agregat anonim dan laporan yang dikirim dengan persetujuan eksplisit.</p></div></main>;

  return <div className={styles.shell}>
    <aside className={`${styles.sidebar} ${menuOpen ? styles.open : ""}`}><div className={styles.logo}><span>NG</span><div><b>NusaGuard</b><small>ADMIN CONSOLE</small></div></div><nav><a className={styles.active} href="#overview">⌂ <span>Ringkasan</span></a><a href="#reports">◇ <span>Laporan masuk</span><em>{data.reports_pending}</em></a><a href="#categories">▥ <span>Kategori</span></a><a href="#system">◉ <span>Status sistem</span></a></nav><div className={styles.sideBottom}><div className={styles.privacyChip}>● PRIVASI AKTIF<small>Analisis bersifat ephemeral</small></div><Link href="/">↗ Buka situs publik</Link><button onClick={logout}>Keluar</button></div></aside>
    <main className={styles.main}><header><button className={styles.menu} onClick={()=>setMenuOpen(v=>!v)}>☰</button><div><p>ADMIN CONSOLE / RINGKASAN</p><h1>Selamat datang, Admin.</h1></div><div className={styles.headerRight}><span className={styles.live}>● SISTEM AKTIF</span><button onClick={()=>void load(key)} aria-label="Muat ulang">↻</button><div className={styles.avatar}>NA</div></div></header>
      {error && <div className={styles.alert}>{error}</div>}
      <section id="overview" className={styles.content}><div className={styles.sectionHead}><div><span>GAMBARAN HARI INI</span><h2>Operasi dalam satu pandangan</h2></div><small>Diperbarui langsung dari API</small></div>
        <div className={styles.metrics}><article><span className={styles.metricIcon}>⌁</span><p>Total analisis</p><strong>{data.total_analyzed.toLocaleString("id-ID")}</strong><small>Agregat sepanjang waktu</small></article><article><span className={styles.metricIcon}>◫</span><p>Laporan sukarela</p><strong>{data.reports_total.toLocaleString("id-ID")}</strong><small>Dikirim dengan persetujuan</small></article><article className={data.reports_pending ? styles.attention : ""}><span className={styles.metricIcon}>!</span><p>Perlu ditinjau</p><strong>{data.reports_pending}</strong><small>{data.reports_pending ? "Menunggu tindakan admin" : "Antrean sudah bersih"}</small></article><article><span className={styles.metricIcon}>✓</span><p>Model aktif</p><strong className={styles.modelName}>{data.model_status}</strong><small>Deteksi siap digunakan</small></article></div>
        <div className={styles.grid}><section id="categories" className={styles.panel}><div className={styles.panelHead}><div><span>DISTRIBUSI DETEKSI</span><h3>Kategori teridentifikasi</h3></div><b>{data.total_analyzed} total</b></div><div className={styles.categoryList}>{categoryRows.map(row=><div key={row.name}><i style={{background:row.color}}/><span>{row.name}</span><div className={styles.bar}><b style={{width:`${row.percent}%`,background:row.color}}/></div><strong>{row.count}</strong><small>{row.percent}%</small></div>)}</div></section>
          <section id="system" className={`${styles.panel} ${styles.systemPanel}`}><div className={styles.panelHead}><div><span>KESEHATAN SISTEM</span><h3>Layanan utama</h3></div><b className={styles.ok}>NORMAL</b></div><div className={styles.systemRow}><i>AI</i><div><b>Mesin deteksi</b><small>{data.model_status}</small></div><span>Operasional</span></div><div className={styles.systemRow}><i>API</i><div><b>Backend FastAPI</b><small>Respons dashboard diterima</small></div><span>Terhubung</span></div><div className={styles.systemRow}><i>DB</i><div><b>Penyimpanan aman</b><small>Hanya agregat & laporan berizin</small></div><span>Terjaga</span></div><div className={styles.privacyNote}><b>Mode privasi</b><p>{data.privacy_mode}</p></div></section>
        </div>
        <section id="reports" className={`${styles.panel} ${styles.reports}`}><div className={styles.panelHead}><div><span>ANTREAN MODERASI</span><h3>Laporan terbaru</h3></div><b>{data.reports_pending} menunggu</b></div>{data.recent_reports.length===0?<div className={styles.empty}><span>✓</span><h4>Belum ada laporan masuk</h4><p>Laporan sukarela dari pengguna akan muncul di sini.</p></div>:<div className={styles.tableWrap}><table><thead><tr><th>Waktu</th><th>Isi laporan</th><th>Kategori</th><th>Status</th><th>Aksi</th></tr></thead><tbody>{data.recent_reports.map(report=><tr key={report.id}><td>{new Date(report.created_at).toLocaleDateString("id-ID",{day:"2-digit",month:"short",year:"numeric"})}</td><td><p>{report.text}</p><small>ID {report.id.slice(0,8)}</small></td><td><span className={styles.categoryTag}>{report.category_suggested}</span></td><td><span className={`${styles.status} ${styles[report.status]}`}>{report.status}</span></td><td>{report.status==="pending"?<div className={styles.actions}><button onClick={()=>void moderate(report.id,"reviewed")} title="Tandai ditinjau">✓</button><button onClick={()=>void moderate(report.id,"rejected")} title="Tolak">×</button></div>:"—"}</td></tr>)}</tbody></table></div>}</section>
      </section><footer><span>NusaGuard Administration</span><span>Privasi pengguna adalah batas sistem, bukan fitur opsional.</span></footer>
    </main>
  </div>;
}

